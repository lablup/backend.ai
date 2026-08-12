"""The runtime variant preset seed sources must not drift apart.

A fresh install seeds ``runtime_variant_presets`` from the manager fixture, the
installer ships its own copy of that fixture, and an upgraded deployment gets
the same rows from the seed migrations. Nothing in the schema ties the three
together, so a preset added to one of them alone leaves the table holding a
different set depending on how the database was created.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest

import ai.backend.install
from ai.backend.manager.models.alembic.versions import (
    e7b3a1f9c2d4_seed_runtime_variant_presets_data as snapshot_seed,
)
from ai.backend.manager.models.alembic.versions import (
    fb5befb44035_seed_enable_prompt_tokens_details_preset as prompt_tokens_seed,
)

_MANAGER_FIXTURE_PATH = Path("fixtures/manager/example-runtime-variant-presets.json")
_INSTALLER_FIXTURE_PATH = (
    Path(ai.backend.install.__file__).parent / "fixtures" / "example-runtime-variant-presets.json"
)


@dataclass(frozen=True, order=True)
class _PresetKey:
    runtime_variant_name: str
    name: str


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
        # A seed migration keeps its rows as module literals, so a new one has to
        # be added here to stay covered. Until it is, the tests report it as drift.
        rows: list[dict[str, Any]] = list(snapshot_seed._SEED_DATA)
        rows.append({
            "runtime_variant_name": prompt_tokens_seed._VARIANT_NAME,
            **prompt_tokens_seed._PRESET_ROW,
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
