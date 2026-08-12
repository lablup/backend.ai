"""The runtime variant preset seed sources must not drift apart.

A fresh install seeds ``runtime_variant_presets`` from the manager fixture, the
installer ships its own copy of that fixture, and an upgraded deployment gets
the same rows from the seed migrations. Nothing in the schema ties the three
together, so a preset added to one of them alone leaves the table holding a
different set depending on how the database was created.
"""

from __future__ import annotations

import ast
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest

import ai.backend.install
import ai.backend.manager.models

_MANAGER_FIXTURE_PATH = Path("fixtures/manager/example-runtime-variant-presets.json")
_INSTALLER_FIXTURE_PATH = (
    Path(ai.backend.install.__file__).parent / "fixtures" / "example-runtime-variant-presets.json"
)
_VERSIONS_DIR = Path(ai.backend.manager.models.__file__).parent / "alembic" / "versions"

# A seed migration embeds its rows as literals, so a new one has to be listed
# here to stay covered. Until it is, the tests below report it as drift.
_SNAPSHOT_MIGRATION = _VERSIONS_DIR / "e7b3a1f9c2d4_seed_runtime_variant_presets_data.py"
_SINGLE_ROW_MIGRATIONS = (
    _VERSIONS_DIR / "fb5befb44035_seed_enable_prompt_tokens_details_preset.py",
)


@dataclass(frozen=True, order=True)
class _PresetKey:
    runtime_variant_name: str
    name: str


def _module_literals(path: Path) -> dict[str, Any]:
    """Module-level literal assignments of a revision, read without importing it."""
    literals: dict[str, Any] = {}
    for node in ast.parse(path.read_text()).body:
        if not isinstance(node, ast.Assign):
            continue
        target = node.targets[0]
        if not isinstance(target, ast.Name):
            continue
        try:
            literals[target.id] = ast.literal_eval(node.value)
        except ValueError:
            continue
    return literals


class TestPresetSeedSources:
    @pytest.fixture
    def fixture_presets(self) -> dict[_PresetKey, dict[str, Any]]:
        rows = json.loads(_MANAGER_FIXTURE_PATH.read_text())["runtime_variant_presets"]
        return {_PresetKey(row["runtime_variant_name"], row["name"]): row for row in rows}

    @pytest.fixture
    def installer_fixture_presets(self) -> dict[_PresetKey, dict[str, Any]]:
        rows = json.loads(_INSTALLER_FIXTURE_PATH.read_text())["runtime_variant_presets"]
        return {_PresetKey(row["runtime_variant_name"], row["name"]): row for row in rows}

    @pytest.fixture
    def seeded_presets(self) -> dict[_PresetKey, dict[str, Any]]:
        rows: list[dict[str, Any]] = json.loads(
            _module_literals(_SNAPSHOT_MIGRATION)["_SEED_DATA_JSON"]
        )
        for path in _SINGLE_ROW_MIGRATIONS:
            literals = _module_literals(path)
            rows.append({
                "runtime_variant_name": literals["_VARIANT_NAME"],
                **literals["_PRESET_ROW"],
            })
        return {_PresetKey(row["runtime_variant_name"], row["name"]): row for row in rows}

    def test_installer_fixture_mirrors_the_manager_fixture(
        self,
        fixture_presets: dict[_PresetKey, dict[str, Any]],
        installer_fixture_presets: dict[_PresetKey, dict[str, Any]],
    ) -> None:
        assert installer_fixture_presets == fixture_presets

    def test_seed_migrations_describe_the_same_presets(
        self,
        fixture_presets: dict[_PresetKey, dict[str, Any]],
        seeded_presets: dict[_PresetKey, dict[str, Any]],
    ) -> None:
        unseeded = sorted(set(fixture_presets) - set(seeded_presets))
        unfixtured = sorted(set(seeded_presets) - set(fixture_presets))
        assert not unseeded, f"presets in the fixture but not in any seed migration: {unseeded}"
        assert not unfixtured, f"presets in a seed migration but not in the fixture: {unfixtured}"

    def test_seeded_values_match_the_fixture(
        self,
        fixture_presets: dict[_PresetKey, dict[str, Any]],
        seeded_presets: dict[_PresetKey, dict[str, Any]],
    ) -> None:
        mismatched = sorted(
            key
            for key, row in seeded_presets.items()
            if key in fixture_presets and row != fixture_presets[key]
        )
        assert not mismatched, f"presets whose seeded values differ from the fixture: {mismatched}"
