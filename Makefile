.PHONY: help init setup db migration dev check format test config model-x notebook label alexa-model alexa-tunnel dnd dnd-off install uninstall

# ONNX Runtime for the Models: cpu (default), amd or nvidia. E.g. `make setup RUNTIME=nvidia`.
RUNTIME ?= cpu
# More extras, e.g. `make setup EXTRAS=google` for Google speakers (needs RUNTIME=cpu).
EXTRAS ?=
UV_EXTRAS := --extra $(RUNTIME) $(addprefix --extra ,$(EXTRAS))
UV_RUN := uv run $(UV_EXTRAS)

# Commands that need secrets run through $(RUN). With the 1Password CLI (`op`)
# installed, `op://` references in .env are filled in; otherwise .env is read as is.
ifneq ($(wildcard .env),)
  ifneq ($(shell command -v op 2>/dev/null),)
    RUN := op run --env-file=.env -- $(UV_RUN)
  else
    RUN := $(UV_RUN) --env-file .env
  endif
else
  RUN := $(UV_RUN)
endif

help:
	@echo "make init NAME=myapp  rename the template (package, commands, docs); run once"
	@echo "make setup   install dependencies (RUNTIME=cpu|amd|nvidia, EXTRAS=google), create config.toml and .env"
	@echo "make check   format check, lint and type check"
	@echo "make test    run the tests"
	@echo "make config  load the private config and say if it is valid"
	@echo "make dev     run the live watcher (Ctrl+C stops it)"
	@echo "make model-x  make Model X's file (train extra)"
	@echo "make notebook  open JupyterLab on the Models' training notebooks (train extra)"
	@echo "make label [PORT=8765]  labeling page for [labeling] on http://localhost:PORT/"
	@echo "make db      start PostgreSQL in Docker (compose.yaml)"
	@echo "make migration MSG=\"...\"  Alembic migration for changed SQLModel tables"
	@echo "make alexa-model  write alexa/interactionModels/custom/en-US.json"
	@echo "make alexa-tunnel  how to open only /alexa with the [alexa_skill] tunnel"
	@echo "make dnd FOR=2h [ALLOW=\"urgent\"] / make dnd-off  Do Not Disturb"
	@echo "make install / make uninstall  run the watcher as a systemd user service"

# TODO(template): run once after making a repo from the template, e.g. `make init NAME=deskwatch`.
init:
	@test -n "$(NAME)" || { echo "Set NAME, e.g. make init NAME=deskwatch"; exit 1; }
	python3 scripts/init.py "$(NAME)"

setup:
	uv sync $(UV_EXTRAS)
	@test -f config.toml || { cp config.example.toml config.toml && echo "Created config.toml; edit it."; }
	@test -f .env || { cp .env.example .env && echo "Created .env; edit it."; }

db:
	docker compose up --detach --wait db

migration:
	@test -n "$(MSG)" || { echo "Set MSG, e.g. make migration MSG=\"add model y table\""; exit 1; }
	@if grep -q '^CAMWATCH_DATABASE_URL=.*@127.0.0.1:5432/' .env 2>/dev/null; then $(MAKE) -s db; fi
	$(RUN) camwatch migration "$(MSG)"
	uv run ruff format src/camwatch/migrations

# Starts the Docker database only when .env points at it.
dev:
	@if grep -q '^CAMWATCH_DATABASE_URL=.*@127.0.0.1:5432/' .env 2>/dev/null; then $(MAKE) -s db; fi
	$(RUN) camwatch watch

check:
	$(UV_RUN) ruff format --check .
	$(UV_RUN) ruff check .
	$(UV_RUN) ty check

format:
	uv run ruff format .
	uv run ruff check --fix .

# Database tests use CAMWATCH_TEST_DATABASE_URL if set, else start PostgreSQL with Testcontainers.
test:
	$(UV_RUN) pytest

config:
	$(RUN) camwatch check-config

# Model X's file: a ready-trained person detector, exported to ONNX (OUT=... to choose where).
model-x:
	uv run --extra train python -m camwatch.models.model_x.model_x_export --output "$(or $(OUT),$(HOME)/.local/share/camwatch/models/model_x.onnx)"

notebook:
	$(UV_RUN) --extra train --group notebook jupyter lab src/camwatch/models

label:
	$(RUN) camwatch label --port $(or $(PORT),8765)

alexa-model:
	$(UV_RUN) camwatch alexa-model

alexa-tunnel:
	@$(UV_RUN) camwatch alexa-tunnel

# Do Not Disturb, read at once by a running watcher (kept in $XDG_STATE_HOME/camwatch).
dnd:
	@test -n "$(FOR)" || { echo "Set FOR, e.g. make dnd FOR=2h"; exit 1; }
	$(UV_RUN) camwatch dnd --for "$(FOR)" $(if $(ALLOW),--allow $(ALLOW))

dnd-off:
	$(UV_RUN) camwatch dnd --off

install:
	$(UV_RUN) camwatch service install --checkout "$(CURDIR)" --runtime $(RUNTIME) $(addprefix --extra ,$(EXTRAS))

uninstall:
	$(UV_RUN) camwatch service uninstall
