"""VoiceStudio Hermes plugin - registers a plugin TTS provider.

Provider name is 'voicestudio' (not a built-in, so it is accepted by the TTS
registry). Set it with:

    hermes config set tts.provider voicestudio

Precedence note from upstream: a `tts.providers.<name>: type: command` entry in
config.yaml wins over a plugin registration, so if the old command bridge keeps
the name 'voicestudio' this plugin will not be used for dispatch. Use a different
provider name for the bridge, or drop the bridge entry.
"""
import logging
from typing import Any, Optional

from agent.tts_provider import DEFAULT_OUTPUT_FORMAT, TTSProvider

from . import client

logger = logging.getLogger(__name__)

# Plugin identifier used for registration and config lookup. The catalog id is
# `voicestudio-tts`: the plain `voicestudio` name belongs to a different plugin (a tool
# client for the same app), so this one cannot reuse it.
_PLUGIN = "voicestudio-tts"
# Pre-rename id, kept so settings written by an older install still resolve.
_PLUGIN_LEGACY = "voicestudio"


class VoiceStudioProvider(TTSProvider):
    """VoiceStudio sidecar backend: POST /generate, voices from GET /profiles.

    The provider is instantiated once at plugin registration with initial settings
    from config.yaml. However, voice selection is resolved dynamically via
    _read_voice_from_config() so that settings changes take effect without
    restarting the gateway.
    """

    def __init__(self, base_url=client.DEFAULT_BASE_URL, voice="", engine="",
                 timeout_s=client.DEFAULT_READ_TIMEOUT_S, warm_path="", release_path=""):
        self._base_url = client.normalize_base_url(base_url)
        self._voice = voice or ""  # Initial voice from config (may become stale)
        self._engine = engine or ""
        self._timeout_s = int(timeout_s or client.DEFAULT_READ_TIMEOUT_S)
        self._warm_path = warm_path or ""
        self._release_path = release_path or ""

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

    # ---- voice catalog (powers the settings dropdown) ----
    def list_voices(self) -> list[dict[str, Any]]:
        return client.list_voices_cached(self._base_url)

    def default_voice(self) -> Optional[str]:
        """Always an id: reads voice from config dynamically so settings changes take effect without restart.

        Resolution order:
        1. Read voice from config.yaml (profile-scoped via get_hermes_home())
        2. Fall back to self._voice (set at registration, may be stale)
        3. If neither, use the first available voice from the app
        """
        voice = self._read_voice_from_config() or self._voice
        if voice:
            return client.resolve_voice(self._base_url, voice) or voice
        voices = self.list_voices()
        return voices[0]["id"] if voices else None

    def _debug(self) -> bool:
        """Check if debug logging is enabled in plugin settings."""
        try:
            from hermes_constants import get_hermes_home
            import yaml
            config_path = get_hermes_home() / "config.yaml"
            with open(config_path, "r", encoding="utf-8") as fh:
                config = yaml.safe_load(fh) or {}
            settings = (config.get("plugins", {}) or {}).get("entries", {}).get("voicestudio", {}).get("settings", {}) or {}
            return bool(settings.get("debug", False))
        except Exception:
            return False

    def _read_voice_from_config(self) -> str:
        """Read the voice setting from config.yaml so changes take effect without plugin re-registration.

        Uses get_hermes_home() from hermes_constants (NOT os.environ) because the
        gateway scopes config per-profile via a contextvar, not an env var.
        """
        try:
            from hermes_constants import get_hermes_home
            hermes_home = get_hermes_home()
            config_path = hermes_home / "config.yaml"
            import yaml
            with open(config_path, "r", encoding="utf-8") as fh:
                config = yaml.safe_load(fh) or {}
            plugins = config.get("plugins", {}) or {}
            entries = plugins.get("entries", {}) or {}
            # New id first; fall back to the pre-rename id so an existing install keeps its voice.
            vs = entries.get(_PLUGIN, {}) or entries.get(_PLUGIN_LEGACY, {}) or {}
            settings = vs.get("settings", {}) or {}
            voice = str(settings.get("voice", "") or "").strip()
            if self._debug():
                import logging
                logging.getLogger(__name__).info("_read_voice_from_config: home=%s voice=%s", hermes_home, voice)
            return voice
        except Exception:
            return ""

    # ---- synthesis ----
    def synthesize(self, text, output_path, *, voice=None, model=None, speed=None,
                   format=DEFAULT_OUTPUT_FORMAT, **extra) -> str:
        """Synthesize text into output_path; returns the written path. Raises on failure.

        Note: ignores any 'voice' param passed by the TTS system. Always uses
        self.default_voice() which reads from config dynamically. This prevents
        the TTS system from overriding the configured voice.
        """
        wanted = self.default_voice()
        profile_id = client.resolve_voice(self._base_url, wanted) or wanted
        result = client.generate(self._base_url, text, profile_id, self._engine, self._timeout_s)
        if result.get("status") != 200:
            err = result.get("error") or "http_error"
            detail = client._decode(result.get("body") or b"")
            raise RuntimeError(
                "VoiceStudio synthesis failed (%s): %s" % (err, str(detail)[:300] or "no body"))
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
        client.api_get(self._base_url, self._warm_path, timeout=client.PROBE_TIMEOUT_S)

    def release(self) -> None:
        if not self._release_path:
            return
        client.api_get(self._base_url, self._release_path, timeout=client.PROBE_TIMEOUT_S)


def register(ctx):
    """Wire the provider into the TTS registry from plugin settings."""
    provider = VoiceStudioProvider(
        base_url=ctx.get_config("base_url", default=client.DEFAULT_BASE_URL),
        voice=ctx.get_config("voice", default=""),
        engine=ctx.get_config("engine", default=""),
        timeout_s=ctx.get_config("timeout_s", default=client.DEFAULT_READ_TIMEOUT_S),
        warm_path=ctx.get_config("warm_path", default=""),
        release_path=ctx.get_config("release_path", default=""),
    )
    ctx.register_tts_provider(provider)
    logger.debug("voicestudio plugin registered: TTS provider '%s'", provider.name)

    def _handle_command(raw_args: str) -> str:
        """Slash command handler: /voicestudio [name|refresh]

        - No args: show current voice and list available voices
        - <name>: set voice by name (updates config.yaml)
        - refresh: fetch voices from app and update plugin.yaml choices
        """
        args = (raw_args or "").strip()
        base_url = ctx.get_config("base_url", default=client.DEFAULT_BASE_URL)
        if not args:
            voices = client.list_voices_cached(base_url)
            names = [v.get("display") or v.get("id") for v in voices]
            current = provider.default_voice()
            return "Current voice: %s\nAvailable: %s" % (current, ", ".join(names))
        if args.lower() == "refresh":
            voices = client.list_voices_cached(base_url, force=True)
            names = [v.get("display") or v.get("id") for v in voices]
            if not names:
                # Never wipe an existing dropdown because the app happened to be closed.
                return ("No voices returned from VoiceStudio (%s). Is the app running "
                        "and does it have saved voices? Dropdown left unchanged." % base_url)
            # Update this plugin's own manifest so the settings dropdown stays in sync. The path is
            # derived from the loaded module, never a hardcoded install dir, so a rename or a
            # different profile layout cannot write outside the plugin.
            try:
                import yaml
                from pathlib import Path
                plugin_path = Path(__file__).resolve().parent / "plugin.yaml"
                with open(plugin_path, "r", encoding="utf-8") as fh:
                    data = yaml.safe_load(fh) or {}
                schema = data.get("config_schema", {}) or {}
                voice_field = schema.get("voice", {}) or {}
                voice_field["choices"] = names
                schema["voice"] = voice_field
                data["config_schema"] = schema
                with open(plugin_path, "w", encoding="utf-8") as fh:
                    yaml.safe_dump(data, fh, default_flow_style=False, allow_unicode=True)
                return "Refreshed %d voices: %s" % (len(names), ", ".join(names))
            except Exception as e:
                return "Fetched %d voices but failed to update plugin.yaml: %s" % (len(names), e)
        # Treat as voice name. ctx.set_config writes only this plugin's settings subtree, atomically;
        # rewriting config.yaml by hand would drop the user's comments and formatting.
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
