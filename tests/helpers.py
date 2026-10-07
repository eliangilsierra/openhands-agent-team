"""Shared helpers for the unit tests of the team's Python scripts.

Run all tests from the repository root:  python -m unittest discover -s tests
"""

from __future__ import annotations

import importlib.util
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FIXTURES = ROOT / "tests" / "fixtures"
ROUTING = ROOT / "skills" / "stack-routing" / "scripts"
DEVELOPMENT = ROOT / "skills" / "development" / "scripts"


def load(directory: Path, name: str):
    """Import a script as a module (scripts are not a package)."""
    if str(directory) not in sys.path:
        sys.path.insert(0, str(directory))
    spec = importlib.util.spec_from_file_location(name, directory / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def git(cwd: Path, *args: str) -> str:
    return subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True).stdout


def temp_repo(files: dict[str, str]) -> tuple[tempfile.TemporaryDirectory, Path]:
    """A git repository with one commit on main containing the given files."""
    holder = tempfile.TemporaryDirectory()
    root = Path(holder.name)
    for name, content in files.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    git(root, "init", "-q", "-b", "main")
    git(root, "config", "user.email", "test@example.org")
    git(root, "config", "user.name", "Test")
    git(root, "config", "commit.gpgsign", "false")
    git(root, "add", ".")
    git(root, "commit", "-q", "--no-verify", "-m", "chore: initial commit")
    return holder, root


def write_tree(root: Path, files: dict[str, str]) -> None:
    for name, content in files.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
