"""The `events` table: one row per Event, with the State, Subject Action and Model Output."""

from datetime import datetime
from typing import Any

from sqlalchemy import Column, DateTime
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, SQLModel

from camwatch.domain import Event, Urgency


class EventRecord(SQLModel, table=True):
    """One stored Event."""

    __tablename__ = "events"  # type: ignore[assignment]

    id: int | None = Field(default=None, primary_key=True)
    at: datetime = Field(sa_column=Column(DateTime(timezone=True), nullable=False))
    kind: str
    urgency: str
    announce: bool
    state: str
    subject_action: str | None = None
    details: dict[str, str] = Field(default_factory=dict, sa_column=Column(JSONB, nullable=False))
    model_output: dict[str, Any] = Field(
        default_factory=dict, sa_column=Column(JSONB, nullable=False)
    )

    @classmethod
    def of(cls, event: Event) -> "EventRecord":
        """The row for `event`."""
        return cls(
            at=event.at,
            kind=event.kind,
            urgency=event.urgency.value,
            announce=event.announce,
            state=event.state,
            subject_action=event.subject_action,
            details=event.details,
            model_output=event.model_output,
        )

    def event(self) -> Event:
        """The Event this row holds."""
        return Event(
            self.kind,
            Urgency(self.urgency),
            self.at,
            dict(self.details),
            self.announce,
            self.state,
            self.subject_action,
            dict(self.model_output),
        )
