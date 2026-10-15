"""The starter training notebook is a valid notebook whose code at least compiles.

Running it needs TensorFlow (the train extra) and labeled clips, so it is not run here.
"""

import ast
import json
from pathlib import Path

NOTEBOOK = Path(__file__).parents[1] / "src/camwatch/models/model_x/model_x_train.ipynb"


def test_the_notebook_is_json_and_every_code_cell_compiles():
    notebook = json.loads(NOTEBOOK.read_text())
    assert notebook["nbformat"] == 4
    code = ["".join(cell["source"]) for cell in notebook["cells"] if cell["cell_type"] == "code"]
    assert code
    for source in code:
        ast.parse(source)
