# VoiceStudio Hermes Plugin — Guide

## What this is

A Hermes TTS plugin that bridges VoiceStudio (a local TTS app) into Hermes Agent. Instead of a hardcoded voice ID in a shell script, the voice becomes a configurable setting with a dropdown in the Hermes settings UI.

## How it works

1. VoiceStudio runs as a local HTTP server (default: `http://127.0.0.1:3900`)
2. The plugin registers a TTS provider named `voicestudio` with Hermes
3. Hermes calls `synthesize()` with text → plugin POSTs to VoiceStudio's `/generate` endpoint → returns WAV audio
4. Voices are fetched from VoiceStudio's `GET /profiles` endpoint
5. The `voice` setting accepts either a voice name or an 8-char hex ID (resolved at synthesis time)

## Installation

### Per profile

```bash
cp -r /path/to/voicestudio ~/.hermes/profiles/<profile>/plugins/voicestudio
hermes plugins enable voicestudio --profile <profile>
hermes config set tts.provider voicestudio --profile <profile>
hermes config unset tts.providers.voicestudio --profile <profile>  # remove old command bridge
hermes config set plugins.entries.voicestudio.settings.voice "VoiceName" --profile <profile>
```

### From GitHub

```bash
hermes plugins install EternalShade3D/voicestudio-hermes-plugin
```

## Configuration

Settings are stored in `config.yaml` under `plugins.entries.voicestudio.settings`:

| Key | Default | Description |
|---|---|---|
| `base_url` | `http://127.0.0.1:3900` | VoiceStudio server URL |
| `voice` | `EternalMita_V3` | Voice name or ID (resolved dynamically) |
| `engine` | (empty) | Engine name; empty = app default |
| `timeout_s` | 180 | Read timeout for generation |
| `warm_path` | (empty) | App path called on read-aloud lease start |
| `release_path` | (empty) | App path called on read-aloud lease release |
| `debug` | false | Enable debug logging for voice resolution |

## Commands

| Command | Description |
|---|---|
| `/voicestudio` | Show current voice and list available voices |
| `/voicestudio <name>` | Set voice by name (resolved dynamically) |
| `/voicestudio refresh` | Fetch voices from app and update dropdown choices |

## Architecture

### Files

- `__init__.py` — Plugin registration, TTS provider implementation, slash commands
- `client.py` — HTTP layer (stdlib only, no VoiceStudio semantics)
- `plugin.yaml` — Plugin manifest and config schema (drives settings UI dropdown)
- `README.md` — Quick reference

### Key design decisions

1. **Dynamic voice resolution**: `default_voice()` reads from `config.yaml` at synthesis time using `get_hermes_home()` (profile-scoped via contextvar, NOT `os.environ`). This ensures settings changes take effect without gateway restart.

2. **Ignore passed voice**: `synthesize()` uses `self.default_voice()` unconditionally, ignoring any `voice` param from the TTS system. This prevents the TTS system from overriding the configured voice.

3. **Name resolution**: `resolve_voice()` converts voice names to profile IDs. 8-char hex IDs pass through unchanged. Names are looked up via `GET /profiles`.

4. **No network in `is_available()`**: Returns `True` if `base_url` is set. No network calls (the settings picker calls this on every paint).

5. **Error handling**: `client.py` never raises. `synthesize()` raises `RuntimeError` on failure, which the desktop app catches and shows as an error notification.

### Per-profile voice isolation

Each Hermes profile has its own `config.yaml` with its own `plugins.entries.voicestudio.settings.voice`. The plugin reads from the profile-scoped home at runtime, so:

- eternalmita bot → uses eternalmita's configured voice
- flash bot → uses flash's configured voice

No cross-contamination.

### Desktop auto-speak fix

The "Read replies aloud" auto-speak feature (`use-auto-speak-replies.ts`) originally passed `profile` from `useComposerScope()`, which is `undefined` for the main bot chat. Fixed by adding a fallback: `knownSessionProfile($sessions.get(), sessionId)` resolves the correct bot profile from the session store.

Similarly, `assistant-message.tsx` (manual "Read aloud" button) uses the same fallback.

## Common issues

### Command bridge shadows the plugin

A `tts.providers.voicestudio: type: command` entry in `config.yaml` wins over the plugin. If both exist, the command bridge (with hardcoded voice) is used. **Remove the command bridge entry** when using the plugin.

### Voice not changing after settings update

The plugin instance is created once at registration. `self._voice` stays stale. Fixed by making `default_voice()` read from config dynamically. If still broken, check that `get_hermes_home()` returns the correct profile home (enable `debug: true` in plugin settings).

### Voice dropdown shows IDs instead of names

The `choices` list in `plugin.yaml` is static. Run `/voicestudio refresh` to update it from the app's current voice list.

### Desktop source changes not taking effect

The desktop app runs from a packaged `app.asar`. Source changes need a rebuild (`npm run build`) and asar swap. Plugin code changes need a gateway restart.

## VoiceStudio server

- Default URL: `http://127.0.0.1:3900`
- Endpoints used: `GET /profiles`, `POST /generate` (form-encoded)
- NOT using `/v1/audio/speech` (OpenAI protocol path, non-deterministic for this app)
- Returns WAV bytes

## License

MIT
