"""State store "postgres": each State entered, in the `states` table (see `camwatch.records`)."""

from collections.abc import Mapping
from typing import Any

from sqlalchemy import Engine
from sqlmodel import Session, col, select

from camwatch.config import Config, ConfigError
from camwatch.interfaces import SavedState
from camwatch.parts.postgres_event_log import upgraded_engine
from camwatch.records.state_record import StateRecord
from camwatch.registry import DEFAULT, STATE_STORE


class PostgresStateStore:
    """Adds a row for each State entered; the newest row is the current State."""

    def __init__(self, db: Engine) -> None:
        """Use `db`, already upgraded (`camwatch.database.upgrade`)."""
        self._db = db

    def save(self, state: SavedState) -> None:
        """Remember `state` as the current State."""
        with Session(self._db) as session:
            session.add(StateRecord.of(state))
            session.commit()

    def last(self) -> SavedState | None:
        """The newest saved State, or None."""
        with Session(self._db) as session:
            row = session.exec(
                select(StateRecord).order_by(col(StateRecord.id).desc()).limit(1)
            ).first()
            return None if row is None else row.saved()


@DEFAULT.part(STATE_STORE, "postgres")
def _create(config: Config, options: Mapping[str, Any]) -> PostgresStateStore:
    if options:
        raise ConfigError("state_store: 'postgres' has no options; its URL is in .env")
    return PostgresStateStore(upgraded_engine())
