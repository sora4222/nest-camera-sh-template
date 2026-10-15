from datetime import UTC, datetime

from camwatch.labeling.clip_labels import ClipLabels

AT = datetime(2026, 1, 1, tzinfo=UTC)


def clips(tmp_path, *names: str) -> ClipLabels:
    for name in names:
        (tmp_path / "clips" / name).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / "clips" / name).write_bytes(b"mp4")
    return ClipLabels(tmp_path / "clips", tmp_path / "labels" / "model_x.csv")


def test_every_mp4_in_the_folder_and_below_needs_a_label(tmp_path):
    labels = clips(tmp_path, "b.mp4", "a.mp4", "day1/c.mp4", "notes.txt")
    assert labels.unlabeled() == ["a.mp4", "b.mp4", "day1/c.mp4"]


def test_a_label_is_saved_in_the_models_csv_and_the_clip_is_done(tmp_path):
    labels = clips(tmp_path, "a.mp4", "b.mp4")
    labels.label("a.mp4", "person", AT)
    labels.label("b.mp4", "nobody", AT)
    assert labels.unlabeled() == []
    assert labels.labeled() == {"a.mp4": "person", "b.mp4": "nobody"}
    lines = (tmp_path / "labels" / "model_x.csv").read_text().splitlines()
    assert lines[0] == "clip,label,labeled_at"


def test_only_unlabeled_clips_in_the_folder_have_a_path(tmp_path):
    labels = clips(tmp_path, "a.mp4")
    assert labels.path("a.mp4") == tmp_path / "clips" / "a.mp4"
    assert labels.path("../secret.mp4") is None
    labels.label("a.mp4", "person", AT)
    assert labels.path("a.mp4") is None
