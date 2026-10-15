"""Spoken text from the Message templates in the private config (`[messages]`)."""

import logging
from collections.abc import Mapping

from camwatch.domain import Event

log = logging.getLogger(__name__)


def message_text(
    templates: Mapping[str, str], names: Mapping[str, str], event: Event
) -> str | None:
    """The template for `event.kind`, filled in.

    It can use `[names]`, the Event's details and `{subject_action}`.

    None when there is no template, or it names something the Event does not have.
    """
    template = templates.get(event.kind)
    if template is None:
        return None
    values = {**names, "subject_action": event.subject_action or "", **event.details}
    try:
        return template.format(**values)
    except (KeyError, IndexError, AttributeError, TypeError, ValueError) as error:
        log.warning("message %r cannot be filled in: %r", event.kind, error)
        return None
