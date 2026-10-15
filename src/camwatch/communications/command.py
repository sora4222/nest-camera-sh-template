"""`camwatch dnd`: turn Do Not Disturb on or off for a running watcher.

`make dnd FOR=2h` and `make dnd-off` call it. It needs no config; it writes
`switches.json` in the state folder, which a running watcher reads.
"""

import argparse
import re
import sys
from datetime import timedelta

from camwatch.clock import Clock, SystemClock
from camwatch.communications.switches import Switches
from camwatch.domain import Urgency

COMMANDS = ("dnd",)
_PART = re.compile(r"(\d+)([dhms])")
_UNITS = {"d": "days", "h": "hours", "m": "minutes", "s": "seconds"}


def parse_duration(text: str) -> timedelta:
    """`2h`, `30m`, `1h30m`, `90s` or `1d` as a time span; ValueError if not like that."""
    text = text.strip().lower()
    parts = _PART.findall(text)
    if not parts or "".join(n + u for n, u in parts) != text:
        raise ValueError(f"not a duration: {text!r} (use e.g. 2h, 30m, 1h30m)")
    span = sum((timedelta(**{_UNITS[u]: int(n)}) for n, u in parts), timedelta())
    if span <= timedelta():
        raise ValueError(f"duration must be more than zero: {text!r}")
    return span


def add_commands(commands: "argparse._SubParsersAction[argparse.ArgumentParser]") -> None:
    """Add `dnd` to the CLI's subparsers."""
    dnd = commands.add_parser("dnd", help="Do Not Disturb: on for a while, off, or show it")
    group = dnd.add_mutually_exclusive_group()
    group.add_argument("--for", dest="duration", help="how long, e.g. 2h, 30m, 1h30m")
    group.add_argument("--off", action="store_true", help="turn Do Not Disturb off")
    dnd.add_argument(
        "--allow",
        nargs="+",
        choices=[*Urgency, "none"],
        help="Urgencies still spoken (default: [communications] dnd_allow)",
    )


def run(args: argparse.Namespace) -> int:
    """Run `dnd` on the switches in the state folder."""
    return run_dnd(Switches.default(), SystemClock(), args.duration, args.off, args.allow)


def run_dnd(
    switches: Switches,
    clock: Clock,
    duration: str | None = None,
    off: bool = False,
    allow: list[str] | None = None,
) -> int:
    """Turn Do Not Disturb on for `duration`, off, or (with neither) say whether it is on."""
    if allow is not None and not duration:
        print("--allow needs --for", file=sys.stderr)
        return 2
    if allow is not None and "none" in allow and len(allow) > 1:
        print("--allow none cannot go with other Urgencies", file=sys.stderr)
        return 2
    if off:
        switches.clear_do_not_disturb()
        print("Do Not Disturb is off.")
        return 0
    if duration:
        try:
            span = parse_duration(duration)
        except ValueError as error:
            print(error, file=sys.stderr)
            return 2
        urgencies = None if allow is None else [Urgency(a) for a in allow if a != "none"]
        switches.set_do_not_disturb(clock.now() + span, urgencies)
    dnd = switches.do_not_disturb(clock.now())
    if dnd is None:
        print("Do Not Disturb is off.")
    else:
        through = (
            "[communications] dnd_allow" if dnd.allow is None else ", ".join(dnd.allow) or "none"
        )
        until = dnd.until.astimezone().strftime("%Y-%m-%d %H:%M %Z")
        print(f"Do Not Disturb until {until}; still spoken: {through}.")
    return 0
