import psycopg

from camwatch.database import upgrade


def tables(conninfo: str) -> set[str]:
    with psycopg.connect(conninfo) as db:
        rows = db.execute("SELECT tablename FROM pg_tables WHERE schemaname = current_schema()")
        return {name for (name,) in rows}


def test_upgrade_makes_the_tables_and_records_the_version(database_url):
    upgrade(database_url)
    assert tables(database_url) == {"events", "states", "alembic_version"}


def test_upgrade_twice_changes_nothing(database_url):
    upgrade(database_url)
    upgrade(database_url)
    assert tables(database_url) == {"events", "states", "alembic_version"}


def test_the_migrations_match_the_sqlmodel_tables(database_url):
    """If this fails, a table in camwatch.records changed: run `make migration MSG=...`."""
    from alembic.autogenerate import compare_metadata  # noqa: PLC0415
    from alembic.migration import MigrationContext  # noqa: PLC0415
    from sqlmodel import SQLModel  # noqa: PLC0415

    import camwatch.records  # noqa: F401, PLC0415
    from camwatch.database import engine  # noqa: PLC0415

    upgrade(database_url)
    with engine(database_url).connect() as connection:
        changes = compare_metadata(MigrationContext.configure(connection), SQLModel.metadata)
    assert changes == []
