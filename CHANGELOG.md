# Changelog

## 1.2.0

- **Settings are read through `ctx.get_config`**, not by opening `config.yaml`: the provider keeps
  the plugin context, so a voice change applies live and the plugin needs no direct file access.
- **PyYAML is now declared.** It was used but never declared, and Hermes does not ship it, so on a
  stock install live voice changes fell back to the stale value and `/voicestudio refresh` failed
  with `No module named 'yaml'`. Settings are read through `ctx.get_config`, and the manifest write
  uses `PyYAML>=6,<7`, declared in `plugin.yaml` and `pyproject.toml`, so the import is a normal
  published dependency instead of a private core module.
- **`/voicestudio refresh` saves the voice list first**, then mirrors it into `plugin.yaml` when
  `sync_dropdown` is on. A failed manifest write no longer loses the list, and an empty app response
  never wipes a known one. The write goes through a temp file and keeps the file's own key order.
- **New `sync_dropdown` setting** (default `false`). Off: the installed folder is never modified and
  voices are picked with `/voicestudio <name>`. On: the names are written into `plugin.yaml` so
  Settings shows a voice list, at the cost of the installed folder showing as changed.
- **Every setting is read live**: `base_url`, `engine`, `timeout_s`, `warm_path` and
  `release_path` come from `ctx.get_config` at the moment they are used, so editing them applies
  without a gateway restart.
- `/voicestudio` with no arguments falls back to the stored list when the app is closed.
- The voice setting is now read from `plugins.entries.voicestudio-tts` only. An install left on the
  pre-rename `voicestudio` entry keeps working after one pick (Settings or `/voicestudio <name>`), since
  reading another plugin's settings is not a supported API.

## 1.1.0

- **Renamed the plugin to `voicestudio-tts`.** The id `voicestudio` belongs to a different plugin (a tool client for the same VoiceStudio app) already listed in the Hermes catalog, so the two cannot share a name. Provider setting is now `tts.provider: voicestudio-tts`; the old `plugins.entries.voicestudio` settings are still read as a fallback.
- `/voicestudio <name>` now writes through `ctx.set_config` instead of rewriting `config.yaml` by hand, so user comments and formatting survive.
- `/voicestudio refresh` locates its own `plugin.yaml` from the loaded module instead of a hardcoded install path, so a renamed or differently-laid-out install still updates the right file.
- Removed an unused private core import (`agent.provider_base.CatalogProviderBase`); catalog validation is now warning-free.

- README/GUIDE: desktop setup corrected to **Settings → Voice → Text to speech → Text-To-Speech Provider → VoiceStudio**, with `/voicestudio refresh` and voice pick as explicit steps
- README/GUIDE: audio retention documented (`tts.keep_generated_audio`, `tts.keep_generated_audio_max_mb`, 100 MB cap, oldest pruned first)
- README: assets compressed 5.1 MB → 561 KB, renamed for SEO (`voicestudio-hermes-plugin-banner.jpg`, `voicestudio-hermes-plugin-settings-panel.png`, `voicestudio-hermes-plugin-install-video-thumbnail.jpg`)
- `.gitignore`: `media/` excluded (originals kept out of the repo)
- README: play-overlay thumbnail added at `assets/youtube_how_to_install_play.png`
- GUIDE: `voice` default corrected to empty, dropdown claims qualified, `resolve_voice()` attributed to `client.py`, unverified ID length claim removed
- GUIDE and README: audio cache documented as the running profile's cache, `cache/audio`, not a fixed machine path
- GUIDE: Hermes minimum stated as `>=0.21` per `plugin.yaml`
- `media/` added to `.gitignore`

## 1.0.0

- Initial release
- TTS provider registration with dynamic voice resolution
- Slash commands: `/voicestudio`, `/voicestudio <name>`, `/voicestudio refresh`
- Per-profile voice isolation via `get_hermes_home()`
- Desktop auto-speak profile fix (main bot chat)
- Debug toggle in plugin settings
- Comprehensive documentation
