# VoiceStudio Hermes plugin

<div align="center">

<a href="https://github.com/EternalShade3D/voicestudio-hermes-plugin/releases/latest"><img src="https://img.shields.io/github/v/release/EternalShade3D/voicestudio-hermes-plugin?style=for-the-badge&labelColor=26282e&label=release&color=41CD52" alt="Latest release"></a>
<a href="https://github.com/EternalShade3D/voicestudio-hermes-plugin/blob/main/LICENSE"><img src="https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge&labelColor=26282e" alt="License: MIT"></a>
<a href="https://github.com/EternalShade3D/voicestudio-hermes-plugin"><img src="https://img.shields.io/github/stars/EternalShade3D/voicestudio-hermes-plugin?style=for-the-badge&labelColor=26282e&label=stars&color=41CD52" alt="Stars"></a>
<a href="https://github.com/EternalShade3D/voicestudio-hermes-plugin"><img src="https://img.shields.io/badge/Hermes-Plugin-3776AB?style=for-the-badge&labelColor=26282e&logo=hermes&logoColor=white" alt="Hermes Plugin"></a>

![Banner](assets/banner.png)

</div>

Connect **VoiceStudio** to your **Hermes Agent** to enable realistic, custom local text-to-speech for your bot responses without scripts or manual voice IDs.

- **Dynamic Voice Discovery:** Automatically imports your local VoiceStudio voice models into a simple dropdown.
- **Per-Profile Setup:** Give different Hermes profiles distinct voices.
- **Zero Scripting Required:** Fully integrated UI configuration and commands.

---

## Quick Preview & Demo

<div align="center">

[![Watch the Walkthrough](https://img.youtube.com/vi/qGd0liG_6vk/maxresdefault.jpg)](https://youtu.be/qGd0liG_6vk)

<a href="https://youtu.be/qGd0liG_6vk"><img src="https://img.shields.io/badge/How_to_install-Hermes_Desktop-FF0000?style=for-the-badge&labelColor=26282e&logo=youtube&logoColor=white" alt="How to install the plugin in Hermes Desktop"></a>

*Click above to watch the setup video.*

</div>

### UI Overview

![Plugin UI](assets/screenshot.png)

---

## Prerequisites

Ensure the following before installation:

- [x] **VoiceStudio** is running locally on your machine.
- [x] You have at least **one custom voice** saved in VoiceStudio.
- [x] **Hermes Agent** `v0.21` or newer.

> **Note:** The plugin queries VoiceStudio live over HTTP (`127.0.0.1:3900`). If VoiceStudio isn't running, available voices cannot be fetched.

---

## Installation

Choose your preferred installation method:

### Option A: Hermes Desktop (Recommended)

1. Open **Hermes Desktop**.
2. Navigate to **Capabilities → Plugins → Install from Git**.
3. Paste repo URL: `https://github.com/EternalShade3D/voicestudio-hermes-plugin.git`
4. Select your target profile and confirm installation.
5. Set **VoiceStudio** as your active TTS Provider in plugin settings.

---

### Option B: Command Line (CLI)

#### 1. Clone into Plugins Folder
Default profile path is `~/.hermes/plugins/`. For a custom profile, target `~/.hermes/profiles/<profile_name>/plugins/`.

* **Linux / macOS:**
  \`\`\`bash
  git clone https://github.com/EternalShade3D/voicestudio-hermes-plugin.git ~/.hermes/plugins/voicestudio
  \`\`\`

* **Windows (PowerShell):**
  \`\`\`powershell
  git clone https://github.com/EternalShade3D/voicestudio-hermes-plugin.git "$env:USERPROFILE\.hermes\plugins\voicestudio"
  \`\`\`

* **Manual (No Git):** Download the `.zip` archive, extract contents to a folder named `voicestudio`, and place it inside your `plugins/` directory.

#### 2. Enable & Select Provider

\`\`\`bash
hermes plugins enable voicestudio
hermes config set tts.provider voicestudio
\`\`\`

---

## Configuration & Usage

1. Ensure VoiceStudio is open.
2. In Hermes, fetch your local voice library:
   \`\`\`bash
   /voicestudio refresh
   \`\`\`
3. Select your voice:
   - **Via GUI:** Go to **Settings → Plugins → VoiceStudio** and pick a model from the **Voice** dropdown.
   - **Via Command:** Run `/voicestudio <voice_name>` directly.

### Speech Options
- **On-Demand:** Click **Read aloud** under any specific bot response.
- **Continuous:** Enable **Read replies aloud** in the desktop app settings to auto-speak every response.

---

## Commands Reference

| Command | Description |
| :--- | :--- |
| `/voicestudio` | Displays current voice settings and available local voices. |
| `/voicestudio <name>` | Quickly switches the active voice profile by name. |
| `/voicestudio refresh` | Re-scans VoiceStudio to update the dropdown list with newly added voices. |

---

## Settings Reference

| Key | Default Value | Description |
| :--- | :--- | :--- |
| `base_url` | `http://127.0.0.1:3900` | Local API server endpoint for VoiceStudio. |
| `voice` | *(User choice)* | Voice selection populated via `/voicestudio refresh`. |
| `engine` | *(Empty)* | Specific TTS engine override if required by your setup. |
| `timeout_s` | `180` | Audio generation request timeout in seconds. |
| `warm_path` / `release_path` | *(Empty)* | Optional hooks triggered before/after read-aloud requests. |
| `debug` | `false` | Enables verbose debug logging for voice resolution. |

---

> [!WARNING]
> If you previously configured an older command-bridge setup, remove the legacy override from your `config.yaml`:
> \`\`\`bash
> hermes config unset tts.providers.voicestudio
> \`\`\`

---

## License

This project is licensed under the [MIT License](LICENSE).
