"""`camwatch migration` (`make migration MSG=...`): an Alembic migration for table changes.

It compares the SQLModel tables with the database at `CAMWATCH_DATABASE_URL`.
"""

import argparse
import sys

from camwatch.config import ConfigError
from camwatch.database import new_migration
from camwatch.parts.postgres_event_log import database_url


def add_command(commands: "argparse._SubParsersAction[argparse.ArgumentParser]") -> None:
    """Add `migration` to the CLI's subparsers."""
    migration = commands.add_parser("migration", help="new Alembic migration for table changes")
    migration.add_argument("message", help="what changed, such as 'add model y table'")


def run(args: argparse.Namespace) -> int:
    """Write the migration into `src/camwatch/migrations/versions`."""
    try:
        new_migration(database_url(), args.message)
    except ConfigError as error:
        print(error, file=sys.stderr)
        return 1
    return 0
