# AGENTS.md — VoiceStudio Hermes Plugin

Auto-loaded by Hermes when operating in this plugin directory.

## Plugin structure

- `__init__.py` — Plugin registration, TTS provider, slash commands
- `client.py` — HTTP layer (stdlib only)
- `plugin.yaml` — Manifest and config schema
- `README.md` — Quick reference
- `GUIDE.md` — Full documentation
- `assets/` — Banner, screenshot, README thumbnail (play-overlay copy)
- `LICENSE` — MIT
- `.gitignore` — Standard Python ignores
- `pyproject.toml` — Project metadata

## Rules

- Voice resolution must use `get_hermes_home()` (profile-scoped), never `os.environ`
- `synthesize()` must ignore passed voice param, always use `default_voice()`
- `is_available()` must not make network calls
- `client.py` must never raise — return error envelopes
- Keep `choices` in plugin.yaml in sync with app voices via `/voicestudio refresh`
- Docs must match `plugin.yaml`. The `voice` field ships as `type: str` with no `choices`, so it is a text field you type. Never state a dropdown without saying the list appears only after `/voicestudio refresh` writes `choices`
- `media/` and `optimized_readme.md` are local only, never pushed
- The Hermes minimum is whatever `requires_hermes` in `plugin.yaml` says. Docs and video narration must state the same number

## Testing

Run from a Hermes profile:
```
hermes plugins enable voicestudio-tts --profile <profile>
hermes config set tts.provider voicestudio-tts --profile <profile>
```
