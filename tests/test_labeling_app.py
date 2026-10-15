import json
from datetime import UTC, datetime

from camwatch.labeling.clip_labels import ClipLabels
from camwatch.labeling.labeling_app import LabelingApp

AT = datetime(2026, 1, 1, tzinfo=UTC)
HOST = "localhost:8765"


def app(tmp_path, *names: str) -> tuple[LabelingApp, ClipLabels]:
    (tmp_path / "clips").mkdir()
    for name in names:
        (tmp_path / "clips" / name).write_bytes(b"mp4 " + name.encode())
    labels = ClipLabels(tmp_path / "clips", tmp_path / "model_x.csv")
    return LabelingApp(labels, ["person", "nobody"], "model_x", now=lambda: AT), labels


def get(labeling: LabelingApp, path: str):
    return labeling.handle("GET", path, b"", HOST)


def post(labeling: LabelingApp, data: object):
    return labeling.handle("POST", "/api/label", json.dumps(data).encode(), HOST)


def test_next_gives_the_first_unlabeled_clip_and_the_labels(tmp_path):
    labeling, _ = app(tmp_path, "b.mp4", "a.mp4")
    answer = json.loads(get(labeling, "/api/next").body)
    assert answer == {
        "clip": "a.mp4",
        "remaining": 2,
        "labels": ["person", "nobody"],
        "model": "model_x",
    }


def test_the_clip_itself_is_served(tmp_path):
    labeling, _ = app(tmp_path, "a b.mp4")
    response = get(labeling, "/clips/a%20b.mp4")
    assert (response.status, response.content_type, response.body) == (
        200,
        "video/mp4",
        b"mp4 a b.mp4",
    )
    assert get(labeling, "/clips/../config.toml").status == 404


def test_labeling_saves_and_moves_on(tmp_path):
    labeling, labels = app(tmp_path, "a.mp4", "b.mp4")
    assert post(labeling, {"clip": "a.mp4", "label": "person"}).status == 200
    assert labels.labeled() == {"a.mp4": "person"}
    assert json.loads(get(labeling, "/api/next").body)["clip"] == "b.mp4"


def test_a_label_not_in_the_list_or_a_bad_body_is_refused(tmp_path):
    labeling, labels = app(tmp_path, "a.mp4")
    assert post(labeling, {"clip": "a.mp4", "label": "cat"}).status == 400
    assert labeling.handle("POST", "/api/label", b"not json", HOST).status == 400
    assert labels.labeled() == {}


def test_a_clip_labeled_already_is_a_conflict(tmp_path):
    labeling, _ = app(tmp_path, "a.mp4")
    post(labeling, {"clip": "a.mp4", "label": "person"})
    assert post(labeling, {"clip": "a.mp4", "label": "nobody"}).status == 409


def test_only_requests_to_this_machine_are_answered(tmp_path):
    labeling, _ = app(tmp_path, "a.mp4")
    assert labeling.handle("GET", "/", b"", "evil.example.com").status == 403
    assert labeling.handle("GET", "/", b"", "127.0.0.1:8765").status == 200
    assert get(labeling, "/nowhere").status == 404
