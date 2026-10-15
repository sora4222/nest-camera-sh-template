"""One virtual motion sensor per message kind, and which sensor a spoken text belongs to."""

import re
import string
from collections.abc import Mapping
from dataclasses import dataclass


@dataclass(frozen=True)
class Sensor:
    """A virtual motion sensor shown in the Alexa app; a routine on it says one message."""

    kind: str
    endpoint_id: str
    name: str


def sensors(templates: Mapping[str, str], app: str = "Camera watch") -> list[Sensor]:
    """A sensor for each message kind in `[messages]`, e.g. "Camera watch on break lasted"."""
    return [
        Sensor(kind, f"camwatch-{kind.replace('_', '-')}", f"{app} {kind.replace('_', ' ')}")
        for kind in templates
    ]


def kind_of(text: str, templates: Mapping[str, str], names: Mapping[str, str]) -> str | None:
    """The message kind whose template could have made `text`, else None."""
    for kind, template in templates.items():
        if re.fullmatch(_pattern(template, names), text):
            return kind
    return None


def _pattern(template: str, known: Mapping[str, str]) -> str:
    out = []
    for literal, field, _spec, _conversion in string.Formatter().parse(template):
        out.append(re.escape(literal))
        if field is not None:
            out.append(re.escape(known[field]) if field in known else ".*?")
    return "".join(out)
