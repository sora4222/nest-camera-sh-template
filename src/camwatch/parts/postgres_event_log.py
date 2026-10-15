"""Event log "postgres": every Event in the `events` table (SQLModel, see `camwatch.records`).

The database URL comes from `CAMWATCH_DATABASE_URL` (in .env); `make db` starts one in
Docker for development. The tables are made by the Alembic migrations, run on start.
"""

import os
from collections.abc import Mapping
from typing import Any

from sqlalchemy import Engine
from sqlalchemy.exc import OperationalError
from sqlmodel import Session, col, select

from camwatch.config import Config, ConfigError
from camwatch.database import engine, upgrade
from camwatch.domain import Event
from camwatch.records.event_record import EventRecord
from camwatch.registry import DEFAULT, EVENT_LOG

URL_ENV = "CAMWATCH_DATABASE_URL"


class PostgresEventLog:
    """Keeps Events in one table, oldest first."""

    def __init__(self, db: Engine) -> None:
        """Use `db`, already upgraded (`camwatch.database.upgrade`)."""
        self._db = db

    def record(self, event: Event) -> None:
        """Store `event`."""
        with Session(self._db) as session:
            session.add(EventRecord.of(event))
            session.commit()

    def recent(self, limit: int) -> list[Event]:
        """Up to `limit` Events, newest first."""
        with Session(self._db) as session:
            rows = session.exec(
                select(EventRecord).order_by(col(EventRecord.id).desc()).limit(limit)
            )
            return [row.event() for row in rows]


def database_url() -> str:
    """`CAMWATCH_DATABASE_URL`, or `ConfigError`."""
    url = os.environ.get(URL_ENV)
    if not url:
        raise ConfigError(f"set {URL_ENV} in .env for PostgreSQL (`make db` starts one)")
    return url


def upgraded_engine() -> Engine:
    """An engine for the database, with every migration applied."""
    url = database_url()
    try:
        upgrade(url)
    except OperationalError as error:
        raise ConfigError(f"PostgreSQL: cannot connect: {error.orig}") from None
    return engine(url)


@DEFAULT.part(EVENT_LOG, "postgres")
def _create(config: Config, options: Mapping[str, Any]) -> PostgresEventLog:
    if options:
        raise ConfigError("event_log: 'postgres' has no options; its URL is in .env")
    return PostgresEventLog(upgraded_engine())
