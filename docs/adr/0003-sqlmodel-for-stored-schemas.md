# SQLModel for every schema that is stored

Each Model's output schema (in `<model_name>_schema.py`), States and Subject Actions are SQLModel classes when they are stored. One class is both the Pydantic schema that checks the values and the SQLAlchemy table Alembic makes migrations from, so a developer changes one file, not two. Schemas that are never stored stay plain Pydantic.

## Considered Options

- **Plain Pydantic plus hand-written SQLAlchemy tables**: two classes to keep in step for every change.
- **JSON column for all Model Output**: no migrations, but no checks and hard to query.
