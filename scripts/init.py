"""Rename the template for a new app: `make init NAME=deskwatch`. Run once.

Moves `src/camwatch` to `src/<name>` and changes `camwatch` to `<name>` (and `CAMWATCH`
to `<NAME>`) in every text file the repo tracks. It deletes nothing; the example States
and Model X stay until you replace them (see the to-do list in README.md).
"""

import re
import subprocess
import sys
from pathlib import Path

OLD = "camwatch"
NAME = re.compile(r"[a-z][a-z0-9_]{1,30}")
SKIP = {".png", ".jpg", ".onnx", ".mp4"}


def tracked(root: Path) -> list[Path]:
    """Files git tracks under `root` (every file, if `root` is not a git checkout)."""
    try:
        out = subprocess.run(
            ["git", "-C", str(root), "ls-files"], capture_output=True, text=True, check=True
        ).stdout
        return [root / line for line in out.splitlines() if line]
    except (OSError, subprocess.CalledProcessError):
        return [p for p in root.rglob("*") if p.is_file() and ".git" not in p.parts]


def rename(root: Path, name: str) -> list[Path]:
    """Rename the package to `name` under `root`; return the files changed."""
    if not NAME.fullmatch(name) or name == OLD:
        raise ValueError(f"{name!r}: use lower case letters, digits and _ (e.g. deskwatch)")
    package = root / "src" / OLD
    if not package.is_dir():
        raise FileNotFoundError(f"{package} not found; was `make init` already run?")
    changed = []
    for path in tracked(root):
        if path.suffix in SKIP or not path.is_file() or path.name == "init.py":
            continue
        try:
            text = path.read_text()
        except UnicodeDecodeError:
            continue
        new = text.replace(OLD, name).replace(OLD.upper(), name.upper())
        if new != text:
            path.write_text(new)
            changed.append(path)
    package.rename(root / "src" / name)
    return changed


def main(argv: list[str]) -> int:
    """`init.py NAME`: rename the checkout this script is in."""
    if len(argv) != 1:
        print("usage: python3 scripts/init.py NAME", file=sys.stderr)
        return 2
    try:
        changed = rename(Path(__file__).resolve().parent.parent, argv[0])
    except (ValueError, FileNotFoundError) as error:
        print(error, file=sys.stderr)
        return 1
    print(f"Renamed to {argv[0]} in {len(changed)} files. Next: `make setup`, then README.md.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
