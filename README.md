# Nest camera smart home template

A template for apps that watch a Nest camera with your own Models and talk through Alexa and Google Home. It is built for personal smart home use.

The app is a state machine. The current **State** picks which **Models** run on each Frame. The **Model Output** then picks the next State. States are announced on speakers, and Alexa voice commands can change them. The words are in [GLOSSARY.md](GLOSSARY.md).

The example app reminds a person at a desk to take a break.

## To do for a new app

1. Click **Use this template** on GitHub, clone the new repo, then run `make init NAME=yourapp`.
2. Run `make setup`, then fill in `config.toml` and `.env`.
3. Write your Models: one folder each in `src/<app>/models/` ([CONTRIBUTE.md](CONTRIBUTE.md#add-a-model)).
4. Write your States: one file each in `src/<app>/states/` ([CONTRIBUTE.md](CONTRIBUTE.md#add-a-state)).
5. Set `[app] start_state`, `[models.*]`, `[states.*]` and `[messages]` in `config.toml`.
6. Replace the example tests: `tests/test_example_states.py` and `tests/test_example_end_to_end.py`.
7. Optional: Alexa commands ([docs/alexa.md](docs/alexa.md)), Google speakers ([docs/google.md](docs/google.md)), labeling and training ([docs/labeling.md](docs/labeling.md), [docs/training.md](docs/training.md)).
8. Run `grep -rn "TODO(template)"` to find every other place to change.

## Quick start (the example)

```sh
make setup
make model-x                 # Model X's file: a ready-trained person finder (train extra)
# put a clip at ~/.local/share/camwatch/clips/example.mp4
make config                  # check config.toml
make dev                     # watch it; the log speaker prints what would be said
```

To use a real camera, see [docs/camera.md](docs/camera.md). To run all day, see [docs/service.md](docs/service.md).

## Docs

- [CONTRIBUTE.md](CONTRIBUTE.md): code layout, adding Models, States and parts
- [docs/camera.md](docs/camera.md): Nest camera or video file
- [docs/alexa.md](docs/alexa.md): voice commands and Alexa speakers
- [docs/google.md](docs/google.md): Google Home speakers
- [docs/labeling.md](docs/labeling.md): label clips for a Model
- [docs/training.md](docs/training.md): train a Model and use it
- [docs/service.md](docs/service.md): run as a service
- [docs/adr/](docs/adr/): decisions
