# VoiceStudio Hermes plugin

![Banner](assets/banner.png)

<a href="https://github.com/EternalShade3D/voicestudio-hermes-plugin/releases/latest"><img src="https://img.shields.io/github/v/release/EternalShade3D/voicestudio-hermes-plugin?style=for-the-badge&labelColor=26282e&label=release&color=41CD52" alt="Latest release"></a>
<a href="https://github.com/EternalShade3D/voicestudio-hermes-plugin/blob/main/LICENSE"><img src="https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge&labelColor=26282e" alt="License: MIT"></a>
<a href="https://github.com/EternalShade3D/voicestudio-hermes-plugin"><img src="https://img.shields.io/github/stars/EternalShade3D/voicestudio-hermes-plugin?style=for-the-badge&labelColor=26282e&label=stars&color=41CD52" alt="Stars"></a>
<a href="https://github.com/EternalShade3D/voicestudio-hermes-plugin"><img src="https://img.shields.io/badge/Hermes-Plugin-3776AB?style=for-the-badge&labelColor=26282e&logo=hermes&logoColor=white" alt="Hermes Plugin"></a>

Plugin TTS provider named `voicestudio`, so the voice is a settings value instead of a hardcoded id in a script.

## Screenshot

![Plugin UI](screenshot.png)

## Install

1. Copy the package to `~/.hermes/plugins/voicestudio/`
2. `hermes plugins enable voicestudio`
3. `hermes config set tts.provider voicestudio`

## Settings

| Key | Default | Meaning |
|---|---|---|
| `base_url` | `http://127.0.0.1:3900` | VoiceStudio app server |
| `voice` | `74d7821c` | Voice id or name; names resolve via `/profiles` |
| `engine` | empty | App's current engine when empty |
| `timeout_s` | 180 | Read timeout for generation |
| `warm_path` / `release_path` | empty | Called on the read-aloud lease on / release; empty = no-op |

## Commands

| Command | Description |
|---|---|
| `/voicestudio` | Show current voice and list available voices |
| `/voicestudio <name>` | Set voice by name (resolved dynamically) |
| `/voicestudio refresh` | Fetch voices from app and update the dropdown choices |

- Hermes gives a plugin with a `config_schema` an automatic settings page. It does not build a voice dropdown from `list_voices()` — the desktop voice picker is ElevenLabs-only plus a static provider list. So you get fields (base_url, voice, engine, timeout), not a picker of the app's Saved voices.
- A `tts.providers.<name>: type: command` entry in `config.yaml` wins over a plugin registration. Pick one: keep auto-speak with the bridge, or go plugin-only.

## License

MIT
