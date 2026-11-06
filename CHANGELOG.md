# Changelog

## Unreleased

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
