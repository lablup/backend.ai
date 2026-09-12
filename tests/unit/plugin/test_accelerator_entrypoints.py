"""
Static loadability check for every ``backendai_accelerator_v21`` entry point.

``tests/unit/plugin/test_entrypoint.py`` only asserts that entry points can be
*extracted* from a BUILD file, never that the target they name actually exists.
That gap is how a real bug survived: the Furiosa package declares
``...furiosa.rngd.plugin:RNGDPlugin`` while the class is named ``RngdPlugin``.
Such a mismatch is fatal rather than cosmetic, because
``ai/backend/common/plugin/__init__.py`` calls ``entrypoint.load()`` with no
exception handling, so one bad entry point aborts the agent's loading of *all*
accelerator plugins.

This check resolves each entry point against the source tree with the ``ast``
module, so it needs neither imports nor an installed package nor any hardware.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from ai.backend.plugin.entrypoint import extract_entrypoints_from_buildscript

ACCELERATOR_GROUP = "backendai_accelerator_v21"

REPO_ROOT = Path(__file__).parents[3]
ACCELERATOR_ROOT = REPO_ROOT / "src/ai/backend/accelerator"


def _build_scripts() -> list[Path]:
    if not ACCELERATOR_ROOT.is_dir():
        return []
    return sorted(ACCELERATOR_ROOT.glob("*/BUILD"))


def _module_source_path(module: str) -> Path | None:
    """Map ``ai.backend.accelerator.x.plugin`` to its file under ``src/``."""
    rel = Path(*module.split("."))
    for candidate in (
        REPO_ROOT / "src" / rel.with_suffix(".py"),
        REPO_ROOT / "src" / rel / "__init__.py",
    ):
        if candidate.is_file():
            return candidate
    return None


def _defines_top_level_name(source_path: Path, name: str) -> bool:
    tree = ast.parse(source_path.read_text())
    for node in tree.body:
        match node:
            case ast.ClassDef(name=defined) | ast.FunctionDef(name=defined):
                if defined == name:
                    return True
            case ast.AsyncFunctionDef(name=defined):
                if defined == name:
                    return True
            case ast.Assign(targets=targets):
                for target in targets:
                    if isinstance(target, ast.Name) and target.id == name:
                        return True
            case ast.ImportFrom(names=aliases) | ast.Import(names=aliases):
                for alias in aliases:
                    if (alias.asname or alias.name.split(".")[0]) == name:
                        return True
    return False


def _all_entrypoints() -> list[tuple[str, str, str, Path]]:
    found: list[tuple[str, str, str, Path]] = []
    for build_script in _build_scripts():
        for item in extract_entrypoints_from_buildscript(ACCELERATOR_GROUP, build_script):
            found.append((item.name, item.module, item.attr, build_script))
    return found


def test_accelerator_build_scripts_are_discoverable() -> None:
    if not ACCELERATOR_ROOT.is_dir():
        pytest.skip("the accelerator sources are not part of this test's sandbox")
    assert _build_scripts(), "no accelerator BUILD file found"


def test_every_accelerator_entrypoint_resolves_to_an_existing_class() -> None:
    if not ACCELERATOR_ROOT.is_dir():
        pytest.skip("the accelerator sources are not part of this test's sandbox")

    failures: list[str] = []
    for name, module, attr, build_script in _all_entrypoints():
        source_path = _module_source_path(module)
        if source_path is None:
            failures.append(f"{name}: module {module!r} has no source file (from {build_script})")
        elif not _defines_top_level_name(source_path, attr):
            failures.append(f"{name}: {module}:{attr} does not exist (defined in {build_script})")

    assert not failures, "broken accelerator entry points:\n  " + "\n  ".join(failures)


def test_the_rngd_entrypoint_matches_its_class() -> None:
    """The specific regression this check exists to prevent."""
    if not ACCELERATOR_ROOT.is_dir():
        pytest.skip("the accelerator sources are not part of this test's sandbox")

    entries = {name: (module, attr) for name, module, attr, _ in _all_entrypoints()}
    assert "rngd" in entries, "the rngd accelerator entry point is missing"
    module, attr = entries["rngd"]
    assert (module, attr) == ("ai.backend.accelerator.furiosa.rngd.plugin", "RngdPlugin")
    source_path = _module_source_path(module)
    assert source_path is not None
    assert _defines_top_level_name(source_path, attr)
