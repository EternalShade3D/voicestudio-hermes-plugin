"""VoiceStudio Hermes plugin - registers a plugin TTS provider.

Plugin id and provider name are 'voicestudio-tts'. The bare 'voicestudio' id is
already taken by a different catalog plugin (a tool client for the same app), so
this one must not reuse it. Set it with:

    hermes config set tts.provider voicestudio-tts

Precedence note from upstream: a `tts.providers.<name>: type: command` entry in
config.yaml wins over a plugin registration, so if an old command bridge keeps
the name 'voicestudio' this plugin will not be used for dispatch. Remove the
bridge entry (`hermes config unset tts.providers.voicestudio`).
"""
import logging
import os
from typing import Any, Optional

from agent.tts_provider import DEFAULT_OUTPUT_FORMAT, TTSProvider

from . import client

logger = logging.getLogger(__name__)

# Plugin identifier used for registration and config lookup. The catalog id is
# `voicestudio-tts`: the plain `voicestudio` name belongs to a different plugin (a tool
# client for the same app), so this one cannot reuse it.
_PLUGIN = "voicestudio-tts"


class VoiceStudioProvider(TTSProvider):
    """VoiceStudio sidecar backend: POST /generate, voices from GET /profiles.

    The provider is instantiated once at plugin registration, but every setting is read
    through the plugin context at use time (``ctx.get_config``), which re-reads the live
    config, so a settings change applies without restarting the gateway. Holding ``ctx`` is
    the supported way to read settings: no YAML parser and no direct file access are involved.
    """

    def __init__(self, base_url=client.DEFAULT_BASE_URL, voice="", engine="",
                 timeout_s=client.DEFAULT_READ_TIMEOUT_S, warm_path="", release_path="",
                 ctx=None):
        self._base_url = client.normalize_base_url(base_url)
        self._voice = voice or ""  # initial value; live reads go through ctx
        self._engine = engine or ""
        self._timeout_s = int(timeout_s or client.DEFAULT_READ_TIMEOUT_S)
        self._warm_path = warm_path or ""
        self._release_path = release_path or ""
        self._ctx = ctx

    # ---- identity ----
    @property
    def name(self) -> str:
        return _PLUGIN

    @property
    def display_name(self) -> str:
        return "VoiceStudio"

    def get_setup_schema(self) -> dict[str, Any]:
        return {"name": self.display_name, "badge": "sidecar", "tag": "voice", "env_vars": []}

    def is_available(self) -> bool:
        """Must not raise and must not make network calls - the picker calls this on every paint."""
        return bool(self._base_url)

    def _base(self) -> str:
        """The server URL from the live settings, so a change applies without a restart."""
        return client.normalize_base_url(str(self._setting("base_url", self._base_url) or self._base_url))

    def _setting(self, key: str, default: Any = None) -> Any:
        """Live read of one plugin setting through the host context."""
        if self._ctx is not None:
            try:
                return self._ctx.get_config(key, default)
            except Exception:
                return default
        return default

    # ---- voice catalog (powers the settings dropdown) ----
    def list_voices(self) -> list[dict[str, Any]]:
        return client.list_voices_cached(self._base())

    def default_voice(self) -> Optional[str]:
        """Always an id: reads the live setting so a change applies without a restart.

        Resolution order:
        1. the current ``voice`` setting (name or id)
        2. the value captured at registration, which may be stale
        3. the first voice the app reports
        """
        voice = str(self._setting("voice", "") or self._voice or "").strip()
        if voice:
            return client.resolve_voice(self._base(), voice) or voice
        voices = self.list_voices()
        return voices[0]["id"] if voices else None

    def _debug(self) -> bool:
        """Whether verbose logging is enabled in plugin settings."""
        return bool(self._setting("debug", False))

    # ---- synthesis ----
    def synthesize(self, text, output_path, *, voice=None, model=None, speed=None,
                   format=DEFAULT_OUTPUT_FORMAT, **extra) -> str:
        """Synthesize text into output_path; returns the written path. Raises on failure.

        Note: ignores any 'voice' param passed by the TTS system. Always uses
        self.default_voice() which reads from config dynamically. This prevents
        the TTS system from overriding the configured voice.
        """
        base = self._base()  # read once, reused for the whole request
        wanted = self.default_voice()
        profile_id = client.resolve_voice(base, wanted) or wanted
        result = client.generate(base, text, profile_id, self._engine, self._timeout_s)
        if result.get("status") != 200:
            # One short, actionable sentence instead of the app's JSON paragraph.
            raise RuntimeError(client.describe_failure(
                result, base, self._timeout_s, voice=profile_id or ""))
        body = result.get("body") or b""
        if isinstance(body, str):
            body = body.encode("utf-8")
        if not body:
            raise RuntimeError("VoiceStudio returned an empty audio body for profile %s" % profile_id)
        # The app answers with WAV bytes. If a different container was asked for, the
        # path must still describe what is actually in it, otherwise ffmpeg/playback
        # misreads the file. Coerce the extension to the real format.
        if client.looks_like_wav(body) and not output_path.lower().endswith(".wav"):
            output_path = output_path.rsplit(".", 1)[0] + ".wav"
        with open(output_path, "wb") as fh:
            fh.write(body)
        return output_path

    # ---- lease hooks (read-aloud on / last lease released) ----
    def warm(self) -> None:
        if not self._warm_path:
            return
        client.api_get(self._base(), self._warm_path, timeout=client.PROBE_TIMEOUT_S)

    def release(self) -> None:
        if not self._release_path:
            return
        client.api_get(self._base(), self._release_path, timeout=client.PROBE_TIMEOUT_S)


def _stored_voices(ctx) -> list:
    """Voice names kept in this plugin's own state file (no YAML, no file writes of our own)."""
    try:
        value = ctx.state.get("voices", [])
    except Exception:
        return []
    return [str(v) for v in value] if isinstance(value, list) else []


def _sync_dropdown(ctx) -> bool:
    """Whether refresh should mirror the names into the manifest. Off unless the user turns it on."""
    value = ctx.get_config("sync_dropdown", default=False)
    if isinstance(value, str):
        return value.strip().lower() not in {"false", "0", "no", "off"}
    return bool(value)


def _write_dropdown_choices(names: list) -> None:
    """Copy the voice names into this plugin's manifest, which is what paints the settings dropdown.

    Uses ``hermes_yaml``, the YAML module Hermes itself ships, so the plugin needs no extra
    dependency. The path comes from the loaded module, never a hardcoded install dir, and the
    write goes through a temp file so an interrupted save cannot truncate the manifest.
    """
    from pathlib import Path

    from hermes_yaml import safe_dump, safe_load

    plugin_path = Path(__file__).resolve().parent / "plugin.yaml"
    with open(plugin_path, "r", encoding="utf-8") as fh:
        data = safe_load(fh) or {}
    schema = data.get("config_schema", {}) or {}
    voice_field = schema.get("voice", {}) or {}
    voice_field["choices"] = names
    schema["voice"] = voice_field
    data["config_schema"] = schema
    tmp_path = plugin_path.with_name(plugin_path.name + ".tmp")
    with open(tmp_path, "w", encoding="utf-8") as fh:
        safe_dump(data, fh, default_flow_style=False, allow_unicode=True, sort_keys=False)
    os.replace(tmp_path, plugin_path)


def register(ctx):
    """Wire the provider into the TTS registry from plugin settings."""
    provider = VoiceStudioProvider(
        base_url=ctx.get_config("base_url", default=client.DEFAULT_BASE_URL),
        voice=ctx.get_config("voice", default=""),
        engine=ctx.get_config("engine", default=""),
        timeout_s=ctx.get_config("timeout_s", default=client.DEFAULT_READ_TIMEOUT_S),
        warm_path=ctx.get_config("warm_path", default=""),
        release_path=ctx.get_config("release_path", default=""),
        ctx=ctx,
    )
    ctx.register_tts_provider(provider)
    logger.debug("voicestudio plugin registered: TTS provider '%s'", provider.name)

    def _handle_command(raw_args: str) -> str:
        """Slash command handler: /voicestudio [name|refresh]

        - No args: show the current voice and list the known voices
        - <name>: set the voice (written through ctx, so config formatting survives)
        - refresh: read the app's voices, store them, and sync the dropdown unless
          ``sync_dropdown`` is false
        """
        args = (raw_args or "").strip()
        base_url = ctx.get_config("base_url", default=client.DEFAULT_BASE_URL)
        if not args:
            voices = client.list_voices_cached(base_url)
            names = [str(v.get("display") or v.get("id")) for v in voices if (v.get("display") or v.get("id"))] or _stored_voices(ctx)
            current = provider.default_voice()
            if not names:
                return ("Current voice: %s\nNo voices known yet. Start VoiceStudio and run "
                        "/voicestudio refresh." % current)
            return "Current voice: %s\nAvailable: %s" % (current, ", ".join(names))
        if args.lower() == "refresh":
            voices = client.list_voices_cached(base_url, force=True)
            names = [str(v.get("display") or v.get("id")) for v in voices if (v.get("display") or v.get("id"))]
            if not names:
                # Never wipe a known list because the app happened to be closed, and say why.
                probe = client.api_get(base_url, client.PROFILES_PATH)
                if probe.get("status") == 200:
                    reason = ("VoiceStudio is running but has no saved voices yet. "
                              "Create or save a voice in the app first.")
                else:
                    reason = client.describe_failure(probe, base_url)
                return "%s Nothing was changed." % reason
            state_note = ""
            try:
                ctx.state.set("voices", names)
            except Exception as exc:
                state_note = " (plugin state not saved: %s)" % exc
            if not _sync_dropdown(ctx):
                return ("Saved %d voices to plugin state%s. Dropdown sync is off "
                        "(sync_dropdown: false); pick one with /voicestudio <name>: %s"
                        % (len(names), state_note, ", ".join(names)))
            try:
                _write_dropdown_choices(names)
            except Exception as exc:
                return ("Saved %d voices to plugin state%s; dropdown not updated (%s). "
                        "Pick one with /voicestudio <name>: %s"
                        % (len(names), state_note, exc, ", ".join(names)))
            return "Refreshed %d voices: %s%s" % (len(names), ", ".join(names), state_note)
        # Treat as a voice name. ctx.set_config writes only this plugin's settings subtree,
        # atomically; rewriting config.yaml by hand would drop the user's comments and formatting.
        try:
            ctx.set_config("voice", args)
            return "Voice set to: %s" % args
        except Exception as e:
            return "Failed to set voice: %s" % e

    try:
        reg = ctx.register_command("voicestudio", _handle_command, description="VoiceStudio TTS commands: /voicestudio <name> or /voicestudio refresh", args_hint="[name|refresh]")
        logger.info("voicestudio: command registration result: %s", reg)
    except Exception as e:
        logger.error("voicestudio: command registration failed: %s", e, exc_info=True)
