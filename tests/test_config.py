from datetime import time
from pathlib import Path

import pytest

from camwatch.config import ConfigError, StateSettings, load_config
from camwatch.domain import Urgency

REPO = Path(__file__).resolve().parent.parent

MINIMAL = """
[app]
start_state = "no_one_at_desk"
"""


def write(tmp_path: Path, text: str) -> Path:
    path = tmp_path / "config.toml"
    path.write_text(text)
    return path


def test_example_config_loads():
    config = load_config(REPO / "config.example.toml")
    assert config.app.start_state == "no_one_at_desk"
    assert config.speakers
    assert config.models["model_x"]["file"] == "models/model_x.onnx"
    assert config.state_settings("person_at_desk").lasted_minutes == 50


def test_minimal_config_turns_everything_off(tmp_path):
    config = load_config(write(tmp_path, MINIMAL))
    assert config.parts.camera == "video_file"
    assert config.parts.event_log == "memory"
    assert config.parts.state_store == "memory"
    assert config.speakers == []
    assert not config.alexa_skill.enabled
    assert config.paths.private_data == Path.home() / ".local/share/camwatch"
    assert config.watcher.check_seconds == 0.25


def test_relative_paths_are_inside_the_private_data_folder(tmp_path):
    config = load_config(write(tmp_path, MINIMAL + '[paths]\nprivate_data = "/nas/watch"\n'))
    assert config.paths.private("models/x.onnx") == Path("/nas/watch/models/x.onnx")
    assert config.paths.private("/elsewhere/x.onnx") == Path("/elsewhere/x.onnx")


def test_a_state_with_no_table_gets_the_defaults(tmp_path):
    config = load_config(write(tmp_path, MINIMAL))
    assert config.state_settings("anything") == StateSettings()


def test_state_settings_are_read(tmp_path):
    text = MINIMAL + '[states.busy]\nurgency = "urgent"\nlasted_minutes = 5\n'
    settings = load_config(write(tmp_path, text)).state_settings("busy")
    assert settings.urgency is Urgency.URGENT
    assert settings.lasted_minutes == 5


def test_watcher_must_check_a_positive_number_of_seconds(tmp_path):
    with pytest.raises(ConfigError, match="check_seconds"):
        load_config(write(tmp_path, MINIMAL + "\n[watcher]\ncheck_seconds = 0\n"))


def test_quiet_hours_are_parsed(tmp_path):
    text = MINIMAL + '[[quiet_hours]]\ndays = ["mon"]\nstart = "22:00"\nend = "07:00"\n'
    (quiet,) = load_config(write(tmp_path, text + 'allow = ["urgent"]\n')).quiet_hours
    assert (quiet.start, quiet.end, quiet.allow) == (time(22, 0), time(7, 0), [Urgency.URGENT])


def test_part_and_model_options_come_from_their_own_tables(tmp_path):
    text = MINIMAL + '[camera]\ndevice = "office"\n[models.model_y]\nfile = "y.onnx"\n'
    config = load_config(write(tmp_path, text))
    assert config.part_options("camera") == {"device": "office"}
    assert config.part_options("presence") == {}
    assert config.models == {"model_y": {"file": "y.onnx"}}


def test_unknown_key_is_an_error(tmp_path):
    with pytest.raises(ConfigError, match="tymers"):
        load_config(write(tmp_path, MINIMAL + "\n[tymers]\n"))


def test_the_start_state_is_needed(tmp_path):
    with pytest.raises(ConfigError, match="start_state"):
        load_config(write(tmp_path, "[app]\n"))


def test_unknown_time_zone_is_an_error(tmp_path):
    with pytest.raises(ConfigError, match="time zone"):
        load_config(write(tmp_path, MINIMAL + 'timezone = "Mars/Base"\n'))


def test_missing_file_is_an_error(tmp_path):
    with pytest.raises(ConfigError, match="make setup"):
        load_config(tmp_path / "config.toml")


def test_path_comes_from_environment(tmp_path, monkeypatch):
    path = write(tmp_path, MINIMAL)
    monkeypatch.setenv("CAMWATCH_CONFIG", str(path))
    assert load_config().app.start_state == "no_one_at_desk"
