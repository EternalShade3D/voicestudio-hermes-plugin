# VoiceStudio Hermes plugin

<a href="https://github.com/EternalShade3D/voicestudio-hermes-plugin/releases/latest"><img src="https://img.shields.io/github/v/release/EternalShade3D/voicestudio-hermes-plugin?style=for-the-badge&labelColor=26282e&label=release&color=41CD52" alt="Latest release"></a>
<a href="https://github.com/EternalShade3D/voicestudio-hermes-plugin/blob/main/LICENSE"><img src="https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge&labelColor=26282e" alt="License: MIT"></a>
<a href="https://github.com/EternalShade3D/voicestudio-hermes-plugin"><img src="https://img.shields.io/github/stars/EternalShade3D/voicestudio-hermes-plugin?style=for-the-badge&labelColor=26282e&label=stars&color=41CD52" alt="Stars"></a>
<a href="https://github.com/EternalShade3D/voicestudio-hermes-plugin"><img src="https://img.shields.io/badge/Hermes-Plugin-3776AB?style=for-the-badge&labelColor=26282e&logo=hermes&logoColor=white" alt="Hermes Plugin"></a>

![Banner](assets/banner.png)

VoiceStudio is a local text-to-speech app. This plugin connects it to Hermes Agent so your bot can speak replies aloud using custom voices you create in VoiceStudio. No hardcoded voice IDs, no shell scripts. Each bot profile gets its own voice. Change it anytime from settings or with `/voicestudio <name>`.

**For:** Hermes users who want text-to-speech with custom voices from VoiceStudio.
**Not for:** Users without VoiceStudio installed (requires the local app running on port 3900).

> **Note:** The settings dropdown starts empty. Run `/voicestudio refresh` once after install to populate it with your VoiceStudio voices. You can also set a voice directly with `/voicestudio <name>`.

## Screenshot

![Plugin UI](assets/screenshot.png)

## Install

1. Copy the package to `~/.hermes/plugins/voicestudio/`
2. `hermes plugins enable voicestudio`
3. `hermes config set tts.provider voicestudio`
4. **Populate your voice dropdown:** open Hermes and run `/voicestudio refresh` — this fetches your VoiceStudio voices and fills the settings dropdown

> **Note:** The `voice` field starts empty. After running `/voicestudio refresh`, your voices appear in the dropdown. You can also set a voice directly with `/voicestudio <name>`.

## Settings

| Key | Default | Meaning |
|---|---|---|
| `base_url` | `http://127.0.0.1:3900` | VoiceStudio app server |
| `voice` | (empty) | Voice name or ID; names resolve via `/profiles`. Run `/voicestudio refresh` to populate dropdown |
| `engine` | (empty) | App's current engine when empty |
| `timeout_s` | 180 | Read timeout for generation |
| `warm_path` / `release_path` | (empty) | Called on the read-aloud lease on / release; empty = no-op |
| `debug` | false | Enable debug logging for voice resolution |

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
