import importlib.util
import shutil
import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).parents[1]
SPEC = importlib.util.spec_from_file_location("init", REPO / "scripts" / "init.py")
assert SPEC and SPEC.loader
init = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(init)


@pytest.fixture
def copy(tmp_path) -> Path:
    files = subprocess.run(
        ["git", "-C", str(REPO), "ls-files"], capture_output=True, text=True, check=True
    ).stdout.splitlines()
    if not files:
        pytest.skip("not a git checkout")
    root = tmp_path / "app"
    for name in files:
        if (REPO / name).is_file():
            (root / name).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(REPO / name, root / name)
    subprocess.run(["git", "init", "-q", str(root)], check=True)
    subprocess.run(["git", "-C", str(root), "add", "-A"], check=True)
    return root


def test_renames_the_package_and_every_mention(copy):
    init.rename(copy, "deskwatch")
    assert (copy / "src" / "deskwatch" / "state.py").is_file()
    assert not (copy / "src" / "camwatch").exists()
    assert 'deskwatch = "deskwatch.cli:main"' in (copy / "pyproject.toml").read_text()
    assert "DESKWATCH_DATABASE_URL" in (copy / ".env.example").read_text()
    leftover = [
        p
        for p in copy.rglob("*")
        if p.is_file()
        and ".git" not in p.parts
        and p.suffix in {".py", ".toml", ".md"}
        and p.name != "init.py"
        and "camwatch" in p.read_text().lower()
    ]
    assert leftover == []


def test_refuses_a_bad_name_or_a_second_run(copy):
    with pytest.raises(ValueError):
        init.rename(copy, "Desk Watch")
    init.rename(copy, "deskwatch")
    with pytest.raises(FileNotFoundError):
        init.rename(copy, "other")
