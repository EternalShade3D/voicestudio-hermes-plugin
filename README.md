# VoiceStudio Hermes plugin

Plugin TTS provider named `voicestudio`, so the voice is a settings value instead of a hardcoded id in a script.

## Verified live (2026-10-22)

- `is_available()` returns True without a network call.
- `get_setup_schema()` returns `{'name': 'VoiceStudio', 'badge': 'sidecar', 'tag': 'voice', 'env_vars': []}`.
- `list_voices()` returned 9 voices from `GET /profiles` (EternalMita_V4 `0edad88b`, EternalMita_V3 `74d7821c`, V2, V1, 4, 2, 1, ref_en_o2_18s, demo).
- `resolve_voice("EternalMita_V3")` → `74d7821c`.
- `synthesize()` wrote 128,684 bytes to `C:\Users\Eternal\.hermes\profiles\system\cache\scratch\plugin_test.wav`.

## Install

Plugins are opt-in: copying files is not enough, the plugin must be enabled.

1. Copy the package to `C:\Users\Eternal\.hermes\plugins\voicestudio\`
2. `hermes plugins enable voicestudio`
3. `hermes config set tts.provider voicestudio`

Hermes gives a plugin with a `config_schema` an automatic settings **page**. It does **not** build a voice dropdown from `list_voices()` — the desktop voice picker is ElevenLabs-only plus a static provider list. So you get fields (base_url, voice, engine, timeout), not a picker of the app's Saved voices.

## Important precedence rule

Upstream: a `tts.providers.<name>: type: command` entry in `config.yaml` **wins over a plugin registration**. Your current provider is the command bridge named `voicestudio`, so as it stands the plugin would be shadowed and never used. Pick one:

- **Keep auto-speak with the bridge** and give the bridge the `{voice}` placeholder so it reads the config value; the plugin then only supplies the voice catalog for the settings UI.
- **Go plugin-only**: remove the `tts.providers.voicestudio` command entry, set `tts.provider: voicestudio`, and rely on `voice.auto_tts` / the Desktop **Read replies aloud** toggle.

## Settings (plugin.yaml config_schema)

| Key | Default | Meaning |
|---|---|---|
| `base_url` | `http://127.0.0.1:3900` | app server |
| `voice` | `74d7821c` | id **or name**; names resolve via `/profiles` |
| `engine` | empty | app's current engine when empty |
| `timeout_s` | 180 | read timeout for generation |
| `warm_path` / `release_path` | empty | called on the read-aloud lease on / release; empty = no-op |

## Contract followed

`agent/tts_provider.py` ABC: `name` (abstract), `synthesize` (abstract, must return the written path and raise on failure), `list_voices` (id required, display/language optional), `default_voice`, `get_setup_schema`, `is_available` (no network, no raise), `warm`/`release` (TTS lease), `voice_compatible` (default False). Route is `POST /generate`, form-encoded — `/v1/audio/speech` is not used because it is the OpenAI-protocol path and is non-deterministic for this app.
