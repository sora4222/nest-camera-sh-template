# camwatch

A smart home app: it watches Nest cameras with Models and talks through Alexa and Google Home speakers. Alexa voice commands can change its State.

- Use the words in [GLOSSARY.md](GLOSSARY.md) in code, docs and commits.
- Keep everything single responsibility: one job per Python file, one Model per folder in `models/`, one State per file in `states/`.
- Places a new app must change are marked `TODO(template):`.
- Use `uv` and `make` (`make check`, `make test`). No private data in git; real values go in `config.toml` and `.env`.
