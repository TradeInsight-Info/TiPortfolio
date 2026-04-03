#!/usr/bin/env python3
"""Bump version in pyproject.toml, commit, create git tag, and push.

Usage:
    python scripts/release.py 0.2.0
    python scripts/release.py patch   # 0.1.0 → 0.1.1
    python scripts/release.py minor   # 0.1.0 → 0.2.0
    python scripts/release.py major   # 0.1.0 → 1.0.0
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

PYPROJECT = Path(__file__).resolve().parent.parent / "pyproject.toml"
VERSION_RE = re.compile(r'^version\s*=\s*"(\d+\.\d+\.\d+)"', re.MULTILINE)


def current_version() -> str:
    text = PYPROJECT.read_text()
    m = VERSION_RE.search(text)
    if not m:
        raise SystemExit("Could not find version in pyproject.toml")
    return m.group(1)


def bump(current: str, part: str) -> str:
    major, minor, patch = (int(x) for x in current.split("."))
    if part == "patch":
        return f"{major}.{minor}.{patch + 1}"
    if part == "minor":
        return f"{major}.{minor + 1}.0"
    if part == "major":
        return f"{major + 1}.0.0"
    raise SystemExit(f"Unknown bump type: {part}")


def run(cmd: list[str]) -> None:
    print(f"  $ {' '.join(cmd)}")
    subprocess.run(cmd, check=True)


def main() -> None:
    if len(sys.argv) != 2:
        print(__doc__)
        raise SystemExit(1)

    arg = sys.argv[1]
    old = current_version()

    if arg in ("patch", "minor", "major"):
        new = bump(old, arg)
    elif re.match(r"^\d+\.\d+\.\d+$", arg):
        new = arg
    else:
        raise SystemExit(f"Invalid version or bump type: {arg}")

    if new == old:
        raise SystemExit(f"Version is already {old}")

    print(f"Bumping {old} → {new}")

    # Update pyproject.toml
    text = PYPROJECT.read_text()
    text = VERSION_RE.sub(f'version = "{new}"', text)
    PYPROJECT.write_text(text)
    print(f"  Updated pyproject.toml")

    # Git commit and tag
    run(["git", "add", "pyproject.toml"])
    run(["git", "commit", "-m", f"release: v{new}"])
    run(["git", "tag", f"v{new}"])
    run(["git", "push"])
    run(["git", "push", "--tags"])

    print(f"\nReleased v{new} — GitHub Actions will publish to PyPI.")


if __name__ == "__main__":
    main()
