# Training a Model

Training is for experiments and is kept apart from the app. The app only runs ONNX files.

1. Label clips ([labeling.md](labeling.md)).
2. Set up the machine that trains (an NVIDIA GPU helps): `make setup RUNTIME=nvidia`.
3. Run `make notebook` and open `models/model_x/model_x_train.ipynb`. It is a starter: it reads the labels, takes frames from each clip, trains a small Keras classifier, holds out whole clips to measure accuracy, and exports to ONNX. Copy it into your Model's folder and change it as needed.
4. Put the `.onnx` file in the private data folder, and set `[models.<name>] file`.
5. Make the Model's `run` read the outputs your export gives, matching its `<name>_schema.py`.

`make model-x` is a different route: it downloads a ready-trained detector (SSD MobileNet, COCO) and exports it.

ONNX Runtime runs on the CPU (`RUNTIME=cpu`), AMD GPUs (`amd`) or NVIDIA GPUs (`nvidia`). Set `runtime = "auto"` in `[models.<name>]` to use whichever is installed.
