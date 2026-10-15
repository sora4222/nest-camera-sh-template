"""The PostgreSQL database: connect, apply the Alembic migrations, and make a new one."""

from pathlib import Path

import psycopg
from alembic import command
from alembic.config import Config
from sqlalchemy import Engine, create_engine

MIGRATIONS = Path(__file__).parent / "migrations"
VERSIONS = MIGRATIONS / "versions"


def engine(url: str) -> Engine:
    """A SQLAlchemy engine for the psycopg URL `url` (`postgresql://...`)."""
    return create_engine("postgresql+psycopg://", creator=lambda: psycopg.connect(url))


def _alembic(connection: object) -> Config:
    config = Config()
    config.set_main_option("script_location", str(MIGRATIONS))
    config.set_main_option("file_template", "%%(rev)s_%%(slug)s")
    config.attributes["connection"] = connection
    return config


def upgrade(url: str) -> None:
    """Apply every migration not yet applied to the database at `url`."""
    db = engine(url)
    try:
        with db.begin() as connection:
            command.upgrade(_alembic(connection), "head")
    finally:
        db.dispose()


def new_migration(url: str, message: str) -> None:
    """Write a migration for the changes between the SQLModel tables and the database.

    The database at `url` must be up to date first (`upgrade`).
    """
    upgrade(url)
    db = engine(url)
    try:
        with db.begin() as connection:
            revision = f"{len(list(VERSIONS.glob('[0-9]*.py'))) + 1:04d}"
            command.revision(
                _alembic(connection), message=message, autogenerate=True, rev_id=revision
            )
    finally:
        db.dispose()
