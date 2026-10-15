"""`camwatch alexa-model` (`make alexa-model`): write the Alexa interaction model file."""

import argparse
import json
import sys
from pathlib import Path

from camwatch.alexa_skill.interaction_model import interaction_model
from camwatch.alexa_skill.run import voice_states
from camwatch.alexa_skill.skill import all_intents
from camwatch.config import ConfigError, load_config

OUT = Path("alexa/interactionModels/custom/en-US.json")


def add_command(commands: "argparse._SubParsersAction[argparse.ArgumentParser]") -> None:
    """Add `alexa-model` to the CLI's subparsers."""
    model = commands.add_parser("alexa-model", help="write the Alexa interaction model file")
    model.add_argument("--config", type=Path, help="config file (default: $CAMWATCH_CONFIG)")
    model.add_argument("--out", type=Path, default=OUT)


def run(args: argparse.Namespace) -> int:
    """Write the model for `[alexa_skill] invocation`, every intent and every State."""
    try:
        invocation = load_config(args.config).alexa_skill.invocation
    except ConfigError as error:
        print(error, file=sys.stderr)
        return 1
    model = interaction_model(invocation, all_intents().values(), voice_states())
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(model, indent=2) + "\n")
    print(f"Wrote {args.out}; paste it into the Alexa developer console (JSON Editor).")
    return 0
