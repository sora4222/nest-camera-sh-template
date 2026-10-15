"""Labels for a folder of clips, one CSV per Model: `labels/<model>.csv` (clip, label, time).

Clips are MP4 files the developer saved from the Google Home app into the clips folder.
A clip's name is its path inside that folder.
"""

import csv
from datetime import datetime
from pathlib import Path

FIELDS = ("clip", "label", "labeled_at")


class ClipLabels:
    """Which clips in `clips` have a label in `file`."""

    def __init__(self, clips: Path, file: Path) -> None:
        """Label the MP4 clips under `clips`, keeping the labels in the CSV `file`."""
        self.clips = clips
        self.file = file

    def labeled(self) -> dict[str, str]:
        """Clip name -> label, for every labeled clip."""
        if not self.file.exists():
            return {}
        with self.file.open(newline="") as rows:
            return {row["clip"]: row["label"] for row in csv.DictReader(rows)}

    def unlabeled(self) -> list[str]:
        """Names of the clips with no label yet, sorted."""
        done = self.labeled()
        found = (p.relative_to(self.clips).as_posix() for p in self.clips.rglob("*.mp4"))
        return sorted(name for name in found if name not in done)

    def path(self, name: str) -> Path | None:
        """The file of the unlabeled clip `name`, or None if there is no such clip."""
        return self.clips / name if name in self.unlabeled() else None

    def label(self, name: str, label: str, at: datetime) -> None:
        """Save `label` for the clip `name`."""
        self.file.parent.mkdir(parents=True, exist_ok=True)
        new = not self.file.exists()
        with self.file.open("a", newline="") as rows:
            writer = csv.DictWriter(rows, FIELDS)
            if new:
                writer.writeheader()
            writer.writerow({"clip": name, "label": label, "labeled_at": at.isoformat()})
