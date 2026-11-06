# Changelog

## Unreleased

- README: dropdown wording corrected, escaped code fences fixed, YouTube shield moved below the video link, heading changed to how-to, duration corrected
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
