"""`camwatch label` (`make label`): serve the labeling page on this machine until Ctrl+C."""

import argparse
import sys
from pathlib import Path

from camwatch.config import ConfigError, load_config
from camwatch.labeling.clip_labels import ClipLabels
from camwatch.labeling.labeling_app import LabelingApp
from camwatch.labeling.labeling_server import make_server


def add_command(commands: "argparse._SubParsersAction[argparse.ArgumentParser]") -> None:
    """Add `label` to the CLI's subparsers."""
    label = commands.add_parser("label", help="label clips for a Model on a local web page")
    label.add_argument("--config", type=Path, help="config file (default: $CAMWATCH_CONFIG)")
    label.add_argument("--port", type=int, default=8765)


def run(args: argparse.Namespace) -> int:
    """Serve the page for `[labeling]` until Ctrl+C."""
    try:
        config = load_config(args.config)
    except ConfigError as error:
        print(error, file=sys.stderr)
        return 1
    settings = config.labeling
    if not settings.labels:
        print("[labeling] labels: list the labels to choose from", file=sys.stderr)
        return 1
    clips = config.paths.private(settings.clips)
    file = config.paths.private(Path("labels") / f"{settings.model}.csv")
    app = LabelingApp(ClipLabels(clips, file), settings.labels, settings.model)
    server = make_server(app, args.port)
    print(f"Labeling {clips} for {settings.model} on http://localhost:{server.server_port}/")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0
