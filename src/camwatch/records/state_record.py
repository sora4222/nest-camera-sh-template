"""The `states` table: each State the app entered, newest last."""

from datetime import datetime

from sqlalchemy import Column, DateTime, Text
from sqlmodel import Field, SQLModel

from camwatch.interfaces import SavedState


class StateRecord(SQLModel, table=True):
    """One State the app entered, with its fields as JSON."""

    __tablename__ = "states"  # type: ignore[assignment]

    id: int | None = Field(default=None, primary_key=True)
    name: str
    data: str = Field(sa_column=Column(Text, nullable=False))
    since: datetime = Field(sa_column=Column(DateTime(timezone=True), nullable=False))

    @classmethod
    def of(cls, state: SavedState) -> "StateRecord":
        """The row for `state`."""
        return cls(name=state.name, data=state.data, since=state.since)

    def saved(self) -> SavedState:
        """The saved State this row holds."""
        return SavedState(self.name, self.data, self.since)
