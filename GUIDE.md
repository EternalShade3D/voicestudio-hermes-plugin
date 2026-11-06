# VoiceStudio Hermes Plugin — Guide

## What this is

A Hermes TTS plugin that bridges VoiceStudio (a local TTS app) into Hermes Agent. Instead of a hardcoded voice ID in a shell script, the voice becomes a configurable setting: a `voice` field you fill with the name you gave the voice in VoiceStudio. The settings field shows it as a list only after `/voicestudio refresh` writes `choices` into `plugin.yaml`.

Hermes minimum: `>=0.21` (`requires_hermes` in `plugin.yaml`). Current Hermes release is 0.23.

Video, how to install in Hermes Desktop: https://youtu.be/qGd0liG_6vk
Release: https://github.com/EternalShade3D/voicestudio-hermes-plugin/releases/tag/v1.0.0

## How it works

1. VoiceStudio runs as a local HTTP server (default: `http://127.0.0.1:3900`)
2. The plugin registers a TTS provider named `voicestudio` with Hermes
3. Hermes calls `synthesize()` with text → plugin POSTs to VoiceStudio's `/generate` endpoint → returns WAV audio
4. Voices are fetched from VoiceStudio's `GET /profiles` endpoint
5. The `voice` setting accepts a voice name or an id. Names are resolved at synthesis time through `GET /profiles`.

## Installation

### Hermes Desktop, recommended

1. Open **Hermes Desktop**.
2. Go to **Capabilities → Plugins → Install from Git**.
3. Paste `https://github.com/EternalShade3D/voicestudio-hermes-plugin.git`.
4. Select the target profile and confirm. Wait for Hermes to finish.
5. In that profile settings, go to **Voice** and choose **VoiceStudio** as the TTS provider.
6. With VoiceStudio open, run `/voicestudio` to list the saved voices, `/voicestudio <name>` to set one.

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
| `voice` | `(empty)` | Voice name or id, resolved dynamically. `plugin.yaml` default is empty |
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
| `/voicestudio refresh` | Fetch voices from the app and write them as `choices` into `plugin.yaml` |

## Architecture

### Files

- `__init__.py` — Plugin registration, TTS provider implementation, slash commands
- `client.py` — HTTP layer (stdlib only), plus `resolve_voice()` which maps saved voice names to ids through `GET /profiles`
- `plugin.yaml` — Plugin manifest and config schema. Ships with no `choices` key, so the settings field is plain text until `/voicestudio refresh` writes `choices`
- `README.md` — Quick reference

### Key design decisions

1. **Dynamic voice resolution**: `default_voice()` reads from `config.yaml` at synthesis time using `get_hermes_home()` (profile-scoped via contextvar, NOT `os.environ`). This ensures settings changes take effect without gateway restart.

2. **Ignore passed voice**: `synthesize()` uses `self.default_voice()` unconditionally, ignoring any `voice` param from the TTS system. This prevents the TTS system from overriding the configured voice.

3. **Name resolution**: `resolve_voice()` in `client.py` maps voice names to profile ids by looking them up through `GET /profiles`. If you already typed an id, it passes through unchanged.

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

### Voice field shows nothing to pick

As shipped `plugin.yaml` has no `choices` key, so the `voice` field is plain text you type. Run `/voicestudio refresh` to write the current voice names into `plugin.yaml` and get a pickable list.

### Desktop source changes not taking effect

The desktop app runs from a packaged `app.asar`. Source changes need a rebuild (`npm run build`) and asar swap. Plugin code changes need a gateway restart.

## Where the audio goes

Every generated reply is written to the cache of the profile that is running the bot: `cache/audio` inside that profile's Hermes home, `~/.hermes/profiles/<profile>/cache/audio`, or `$HERMES_HOME/cache/audio` when `HERMES_HOME` is set. Files are named `tts_<timestamp>` with the extension the app returns.

Each profile keeps its own audio cache, so two bots with the plugin do not share audio. Nothing is written into the plugin folder.

## VoiceStudio server

- Default URL: `http://127.0.0.1:3900`
- Endpoints used: `GET /profiles`, `POST /generate` (form-encoded)
- NOT using `/v1/audio/speech` (OpenAI protocol path, non-deterministic for this app)
- Returns WAV bytes

## License

MIT
