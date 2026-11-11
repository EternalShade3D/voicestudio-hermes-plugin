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

- Read live plugin settings through `ctx.get_config`; do not open `config.yaml` or use `get_hermes_home()` for configuration.
- `synthesize()` must ignore passed voice param, always use `default_voice()`
- `is_available()` must not make network calls
- `client.py` must never raise — return error envelopes
- `/voicestudio refresh` stores voice names in plugin state by default. Only mirror them into `plugin.yaml` when `sync_dropdown: true`; this opt-in write makes the installed plugin folder appear modified.
- Docs must match `plugin.yaml`. The `voice` field ships as `type: str` with no `choices`, so it is plain text by default. Describe a dropdown only when `sync_dropdown: true` is enabled and refresh writes `choices`.
- The current implementation uses maintainer-approved `hermes_yaml.safe_load/safe_dump`. The accepted alternative is a declared `PyYAML>=6,<7` dependency; never leave a YAML import undeclared.
- A successful empty `/profiles` response is different from an unavailable app. Forced refresh must not report stale cached voices as fresh, and failed refreshes must not erase plugin-state voices.
- `media/` and `optimized_readme.md` are local only, never pushed
- The Hermes minimum is whatever `requires_hermes` in `plugin.yaml` says. Docs and video narration must state the same number

## Testing

Run plugin validation, then test from a Hermes profile:
```
hermes plugins validate <plugin-directory>
hermes plugins enable voicestudio-tts --profile <profile>
hermes config set tts.provider voicestudio-tts --profile <profile>
```
