"""Command line entry point: `camwatch <command>`. Make targets call these."""

import argparse
import sys
from pathlib import Path

from camwatch import migration_command
from camwatch.alexa_skill import command as alexa_command
from camwatch.alexa_skill import model_command as alexa_model_command
from camwatch.communications import command as dnd_command
from camwatch.config import ConfigError, load_config
from camwatch.labeling import command as label_command
from camwatch.registry import (
    CAMERA,
    COMMUNICATIONS,
    EVENT_LOG,
    MODEL,
    PRESENCE,
    SPEAKER,
    STATE_STORE,
    default_registry,
)
from camwatch.service import command as service_command
from camwatch.state_registry import all_states
from camwatch.watcher import command as watch_command


def _check_config(path: Path | None) -> int:
    """Load the config and show which chosen parts, Models and States are available."""
    try:
        config = load_config(path)
    except ConfigError as error:
        print(error, file=sys.stderr)
        return 1
    registry = default_registry()
    chosen = [
        (CAMERA, config.parts.camera),
        (EVENT_LOG, config.parts.event_log),
        (STATE_STORE, config.parts.state_store),
        (PRESENCE, config.parts.presence),
        (COMMUNICATIONS, config.parts.communications),
        *((SPEAKER, speaker.kind) for speaker in config.speakers),
        *((MODEL, name) for name in watch_command.used_models()),
    ]
    print("Config is valid.")
    for slot, name in chosen:
        state = "available" if name in registry.names(slot) else "not available yet"
        print(f"  {slot.kind}: {name} ({state})")
    states = all_states()
    start = config.app.start_state
    print(
        f"  states: {', '.join(states)}; start: {start} ({'ok' if start in states else 'unknown'})"
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    """Run a command and return its exit code."""
    parser = argparse.ArgumentParser(prog="camwatch")
    commands = parser.add_subparsers(dest="command", required=True)
    check = commands.add_parser("check-config", help="load the private config and check it")
    check.add_argument("--config", type=Path, help="config file (default: $CAMWATCH_CONFIG)")
    modules = {
        "watch": watch_command,
        "label": label_command,
        "dnd": dnd_command,
        "service": service_command,
        "alexa-tunnel": alexa_command,
        "alexa-model": alexa_model_command,
        "migration": migration_command,
    }
    for module in dict.fromkeys(modules.values()):
        if hasattr(module, "add_commands"):
            module.add_commands(commands)
        else:
            module.add_command(commands)
    args = parser.parse_args(argv)
    if args.command == "check-config":
        return _check_config(args.config)
    return modules[args.command].run(args)


if __name__ == "__main__":
    sys.exit(main())
