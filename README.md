# VoiceStudio Hermes plugin

<a href="https://github.com/EternalShade3D/voicestudio-hermes-plugin/releases/latest"><img src="https://img.shields.io/github/v/release/EternalShade3D/voicestudio-hermes-plugin?style=for-the-badge&labelColor=26282e&label=release&color=41CD52" alt="Latest release"></a>
<a href="https://github.com/EternalShade3D/voicestudio-hermes-plugin/blob/main/LICENSE"><img src="https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge&labelColor=26282e" alt="License: MIT"></a>
<a href="https://github.com/EternalShade3D/voicestudio-hermes-plugin"><img src="https://img.shields.io/github/stars/EternalShade3D/voicestudio-hermes-plugin?style=for-the-badge&labelColor=26282e&label=stars&color=41CD52" alt="Stars"></a>
<a href="https://github.com/EternalShade3D/voicestudio-hermes-plugin"><img src="https://img.shields.io/badge/Hermes-Plugin-3776AB?style=for-the-badge&labelColor=26282e&logo=hermes&logoColor=white" alt="Hermes Plugin"></a>

![Banner](assets/banner.png)

VoiceStudio is a local text-to-speech app. This plugin lets Hermes Agent speak its replies using **your own voices** from VoiceStudio.

No hardcoded voice IDs. No shell scripts. One dropdown, built from the voices you already made in the app. Each bot profile can use a different voice.

## Screenshot

![Plugin UI](assets/screenshot.png)

## Before you install

- [ ] VoiceStudio is installed and **open** on your machine
- [ ] You have **at least one voice saved** in VoiceStudio
- [ ] Hermes Agent 0.21 or newer

The plugin reads your voice list live from the running app, so if VoiceStudio is closed it has nothing to show.

## Install

Pick your profile: `~/.hermes/plugins/` is the default profile. For another profile use `~/.hermes/profiles/<name>/plugins/`.

**1. Get the plugin into your plugins folder**

```bash
git clone https://github.com/EternalShade3D/voicestudio-hermes-plugin.git ~/.hermes/plugins/voicestudio
```

On Windows PowerShell:

```powershell
git clone https://github.com/EternalShade3D/voicestudio-hermes-plugin.git "$env:USERPROFILE\.hermes\plugins\voicestudio"
```

No git? Download the ZIP, extract it, rename the folder to `voicestudio`, and move it into your `plugins/` folder.

**2. Enable it**

```bash
hermes plugins enable voicestudio
```

**3. Make it the TTS provider**

```bash
hermes config set tts.provider voicestudio
```

**4. Load your voices (VoiceStudio must be running)**

In Hermes:

```
/voicestudio refresh
```

This fetches every voice in your VoiceStudio library and fills the plugin's dropdown. If it reports 0 voices, VoiceStudio is not running or has no saved voices yet.

**5. Pick your voice**

Open **Settings → Plugins → VoiceStudio** and choose a voice from the `voice` dropdown. Save.

That's it. Your bot now speaks with the voice you picked.

## How to use

- **One reply:** click **Read aloud** under any bot message
- **Every reply:** turn on **Read replies aloud** in the desktop app

Each Hermes profile has its own `voice` setting, so two bots can speak with two different voices.

## Settings

| Key | Default | Meaning |
|---|---|---|
| `base_url` | `http://127.0.0.1:3900` | VoiceStudio app server. Change if your app listens elsewhere |
| `voice` | (your pick) | Dropdown filled by `/voicestudio refresh` |
| `engine` | (empty) | Engine name when the app needs one; empty uses the app's current engine |
| `timeout_s` | 180 | Read timeout in seconds for generation |
| `warm_path` / `release_path` | (empty) | Optional app path called when read-aloud starts / stops; empty = no-op |
| `debug` | false | Verbose logging for voice resolution |

## Commands

| Command | Description |
|---|---|
| `/voicestudio` | Show the current voice and list the voices found in the app |
| `/voicestudio <name>` | Set the voice by name, without opening Settings |
| `/voicestudio refresh` | Re-read the app's voices and update the dropdown (run this when you add a new voice in VoiceStudio) |

> **Warning:** a `tts.providers.voicestudio: type: command` entry in `config.yaml` overrides this plugin. If you used the old command-bridge setup, remove it first:
> `hermes config unset tts.providers.voicestudio`

## License

MIT
