from pathlib import Path

from camwatch.cli import main

REPO = Path(__file__).resolve().parent.parent


def test_check_config_accepts_example_and_lists_parts(capsys):
    assert main(["check-config", "--config", str(REPO / "config.example.toml")]) == 0
    out = capsys.readouterr().out
    assert "presence: off (available)" in out
    assert "camera: video_file (available)" in out
    assert "communications: standard (available)" in out
    assert "model: model_x (available)" in out
    assert "start: no_one_at_desk (ok)" in out


def test_check_config_reports_bad_file(tmp_path, capsys):
    bad = tmp_path / "config.toml"
    bad.write_text("[parts]\n")
    assert main(["check-config", "--config", str(bad)]) == 1
    assert "app: Field required" in capsys.readouterr().err


def test_check_config_says_when_the_start_state_is_unknown(tmp_path, capsys):
    config = tmp_path / "config.toml"
    config.write_text('[app]\nstart_state = "nowhere"\n')
    assert main(["check-config", "--config", str(config)]) == 0
    assert "start: nowhere (unknown)" in capsys.readouterr().out


def test_alexa_model_writes_the_interaction_model(tmp_path):
    out = tmp_path / "en-US.json"
    config = REPO / "config.example.toml"
    assert main(["alexa-model", "--config", str(config), "--out", str(out)]) == 0
    assert '"invocationName": "camera watch"' in out.read_text()
