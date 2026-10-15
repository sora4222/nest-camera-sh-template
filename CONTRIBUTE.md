# Contributing

Rules are in [CLAUDE.md](CLAUDE.md). Run `make check` and `make test` before each commit.

## How a Frame flows

```
camera -> State machine -> Models the State wants -> Model Output -> State.next()
       -> next State + Events -> event log -> communications -> speakers
```

`watcher/watcher.py` runs this once per `[watcher] check_seconds`. Entering, leaving and staying in a State make Events (`<state>_entered`, `_left`, `_lasted`, `_reminder`). An Event is said only if `[messages]` has a template for it.

## Add a Model

1. Make a folder `src/camwatch/models/model_y/`.
2. Write `model_y_schema.py`: an SQLModel class for what it gives back.
3. Write `model_y.py`: a class with `run(frame, output)` returning that schema, and a factory:
   ```python
   @DEFAULT.part(MODEL, "model_y")
   def _create(config: Config, options: Mapping[str, Any]) -> ModelY:
       return ModelY(config.paths.private(options["file"]))
   ```
4. Import it in `src/camwatch/models/__init__.py`.
5. Add `[models.model_y]` to `config.example.toml` and a test in `tests/`.

A Model can read earlier Models' output with `output.get("model_x", ModelXOutput)`.

## Add a State

1. Make a file `src/camwatch/states/<name>.py` with a `State` subclass and `@register_state`.
2. Set `name`, `models` (Model name -> every Nth Frame) and, if Alexa may set it, `voice_names`.
3. Write `next(output)`: return `Transition(next_state, events, subject_action)`. Return `Transition(self)` to stay.
4. Fields on the State are kept between Frames. The State is saved when the app moves into it, and comes back after a restart.
5. Import it in `src/camwatch/states/__init__.py`. Add `[states.<name>]` and its `[messages]`.

## Add a part

Cameras, event logs, State stores, presence checks and speakers are swappable parts in `src/camwatch/parts/`, one per file. Register a factory with `@DEFAULT.part(SLOT, "name")`, import it in `parts/__init__.py`, and choose it in `[parts]` or `[[speakers]]`. `make config` lists what is available.

## Database

`event_log` and `state_store` "postgres" keep tables in `src/camwatch/records/`. After changing a table, run `make migration MSG="..."`. Tests use `CAMWATCH_TEST_DATABASE_URL`, or start PostgreSQL with Testcontainers.

## Code layout

```
src/camwatch/
  watcher/           the live loop and `camwatch watch`
  state.py           State base class and Transition
  state_machine.py   moves between States, saves them, runs their Models
  state_timers.py    _lasted and _reminder Events
  model_output.py    what the Models gave for one Frame
  model_runner.py    runs the Models a State wants
  models/            one folder per Model (model_x: example person finder)
  states/            one file per State (the desk example)
  parts/             cameras, event logs, State stores, speakers, communications
  records/           database tables (SQLModel)
  communications/    Quiet Hours, Do Not Disturb, message templates
  alexa_skill/       voice commands (custom_intents.py is yours)
  alexa_smart_home/  Alexa routines as speakers
  speech/            Piper speech for Google speakers
  labeling/          the labeling page
  service/           systemd user service
```
