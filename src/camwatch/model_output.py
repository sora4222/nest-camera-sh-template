"""Model Output: everything the Models gave back for one Frame.

Models run in order; each one can read what the earlier ones gave (for example Model Y
reads the box Model X found).
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel

from camwatch.domain import Frame


class ModelOutput:
    """The Frame and each Model's output for it, by Model name."""

    def __init__(self, frame: Frame) -> None:
        """No Model has run on `frame` yet."""
        self.frame = frame
        self._outputs: dict[str, BaseModel] = {}

    @property
    def at(self) -> datetime:
        """When the Frame was taken."""
        return self.frame.taken_at

    def add(self, model: str, output: BaseModel) -> None:
        """Keep what the Model named `model` gave back."""
        self._outputs[model] = output

    def get[T: BaseModel](self, model: str, schema: type[T]) -> T | None:
        """What `model` gave back, checked to be a `schema`; None if it did not run."""
        output = self._outputs.get(model)
        if output is None:
            return None
        if not isinstance(output, schema):
            raise TypeError(
                f"model {model!r} gave a {type(output).__name__}, not {schema.__name__}"
            )
        return output

    def names(self) -> list[str]:
        """Names of the Models that ran, in the order they ran."""
        return list(self._outputs)

    def to_json(self) -> dict[str, Any]:
        """Every output as JSON values, for the event log."""
        return {name: output.model_dump(mode="json") for name, output in self._outputs.items()}
