"""Alembic environment: run the migrations on the connection `camwatch.database` passes in.

`make migration` compares the SQLModel tables in `camwatch.records` with the database.
"""

from alembic import context
from sqlmodel import SQLModel

import camwatch.records  # noqa: F401  (puts the tables in SQLModel.metadata)

context.configure(
    connection=context.config.attributes["connection"], target_metadata=SQLModel.metadata
)
with context.begin_transaction():
    context.run_migrations()
