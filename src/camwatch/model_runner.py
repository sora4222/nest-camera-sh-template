"""Run the Models a State wants on one Frame, in order, into one Model Output."""

import logging
from collections.abc import Mapping

from camwatch.domain import Frame
from camwatch.interfaces import Model
from camwatch.model_output import ModelOutput

log = logging.getLogger(__name__)


class ModelRunner:
    """Holds every Model the app has, by name."""

    def __init__(self, models: Mapping[str, Model]) -> None:
        """`models`: Model name -> Model."""
        self._models = dict(models)

    def run(self, frame: Frame, number: int, wanted: Mapping[str, int]) -> ModelOutput:
        """Run each Model in `wanted` whose `every_frame` divides the Frame `number`.

        A Model that fails is logged and left out of the Model Output.
        """
        output = ModelOutput(frame)
        for name, every_frame in wanted.items():
            if number % max(1, every_frame):
                continue
            model = self._models.get(name)
            if model is None:
                raise KeyError(f"no Model called {name!r} was made; is it in [models]?")
            try:
                output.add(name, model.run(frame, output))
            except Exception:
                log.exception("Model %s failed on this Frame", name)
        return output
