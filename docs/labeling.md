# Labeling clips

1. Save clips from the Google Home app (event history, then download) into the clips folder: `[labeling] clips`, inside the private data folder. Subfolders are fine.
2. Choose the Model and the labels:

   ```toml
   [labeling]
   model = "model_y"
   labels = ["on instagram", "working", "nobody"]
   ```

3. Run `make label` and open http://localhost:8765/. Press 1 to 9 to pick a label.

Labels are saved in `labels/<model>.csv` in the private data folder (clip, label, time). The page only answers on this machine. Labeled clips are not shown again; to change one, edit the CSV.
