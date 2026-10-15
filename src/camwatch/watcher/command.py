"""`camwatch watch` (`make dev`): run the live watcher until stopped, one per machine.

The last saved State is picked up again at startup. With `[alexa_skill] enabled`, the
Alexa skill endpoint runs alongside it (docs/alexa.md).
"""

import argparse
import logging
import os
import sys
from collections.abc import Callable, Mapping
from datetime import timedelta
from pathlib import Path

from camwatch.alexa_skill.run import alexa_app, serve_in_background
from camwatch.clock import Clock, SystemClock
from camwatch.config import Config, ConfigError, load_config
from camwatch.model_runner import ModelRunner
from camwatch.registry import Registry, build_models, build_parts, default_registry
from camwatch.state_machine import StateMachine
from camwatch.state_registry import all_states
from camwatch.state_requests import StateRequests
from camwatch.watcher.watcher import Watcher
from camwatch.watcher_lock import (
    UnsafeLockPath,
    WatcherAlreadyRunning,
    WatcherLock,
    default_lock_path,
)

log = logging.getLogger(__name__)


def add_command(commands: "argparse._SubParsersAction[argparse.ArgumentParser]") -> None:
    """Add `watch` to the CLI's subparsers."""
    watch = commands.add_parser("watch", help="watch the camera live until stopped")
    watch.add_argument("--config", type=Path, help="config file (default: $CAMWATCH_CONFIG)")


def run(args: argparse.Namespace) -> int:
    """Load the config and run the watcher; Ctrl+C stops it."""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s: %(message)s")
    try:
        return start_watcher(load_config(args.config), default_registry())
    except ConfigError as error:
        print(error, file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        return 0


def used_models() -> list[str]:
    """Every Model any State runs, in the order they are first listed."""
    names: dict[str, None] = {}
    for state in all_states().values():
        names.update(dict.fromkeys(state.models))
    return list(names)


def start_watcher(
    config: Config,
    registry: Registry,
    clock: Clock | None = None,
    stop: Callable[[], bool] = lambda: False,
    environ: Mapping[str, str] | None = None,
) -> int:
    """Take the watcher lock, make the parts and watch until `stop()` is true.

    `environ` (default: the process's) gives the Alexa skill ID.
    """
    clock = clock or SystemClock()
    try:
        with WatcherLock(config.paths.lock_file or default_lock_path()):
            parts = build_parts(config, registry)
            runner = ModelRunner(build_models(config, registry, used_models()))
            machine = StateMachine.resume(
                start_name=config.app.start_state,
                now=clock.now(),
                store=parts.state_store,
                runner=runner,
                settings=config.state_settings,
            )
            requests = StateRequests()
            env = os.environ if environ is None else environ
            app = alexa_app(config, parts.event_log, clock, env, status=machine, requests=requests)
            if app is not None:
                serve_in_background(app, config.alexa_skill)
            Watcher(
                camera=parts.camera,
                machine=machine,
                event_log=parts.event_log,
                communications=parts.communications,
                clock=clock,
                offline_after=timedelta(minutes=config.watcher.camera_offline_minutes),
                check_seconds=config.watcher.check_seconds,
                requests=requests,
            ).run(stop)
    except (WatcherAlreadyRunning, UnsafeLockPath) as error:
        print(error, file=sys.stderr)
        return 1
    return 0
