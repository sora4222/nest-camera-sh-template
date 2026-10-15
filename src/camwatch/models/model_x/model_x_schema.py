"""What Model X gives back for one Frame.

TODO(template): change these fields to what your Model gives back. Add `table=True`
(and an Alembic migration, `make migration`) if you want every output stored.
"""

from sqlmodel import Field, SQLModel


class Found(SQLModel):
    """One thing Model X found, such as a person."""

    label: str
    score: float
    box: tuple[float, float, float, float]
    """Left, top, right, bottom as fractions of the Frame size."""


class ModelXOutput(SQLModel):
    """Everything Model X found in one Frame."""

    found: list[Found] = Field(default_factory=list)

    def has(self, label: str) -> bool:
        """Whether something with `label` was found."""
        return any(item.label == label for item in self.found)
