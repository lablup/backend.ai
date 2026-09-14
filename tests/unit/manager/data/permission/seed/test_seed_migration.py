"""The migration writes the rows the fixture holds, down to the id.

A database seeded from the fixture and one carried here by the migration have to end
up the same, or the seed says one thing and a running system another.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

import pytest

_REVISION = "f4a1c9d20b73_sync_seed_roles_with_their_declaration"
_REPOSITORY = Path(__file__).resolve().parents[6]
_VERSIONS = _REPOSITORY / "src/ai/backend/manager/models/alembic/versions"


@pytest.fixture(scope="module")
def migration() -> Any:
    """The revision, imported by path: `versions/` is not a package."""
    spec = importlib.util.spec_from_file_location(_REVISION, _VERSIONS / f"{_REVISION}.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[_REVISION] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def fixture() -> dict[str, Any]:
    path = _REPOSITORY / "fixtures/manager/example-roles.json"
    return json.loads(path.read_text(encoding="utf-8"))


class TestMigrationMatchesFixture:
    def test_presets(self, migration: Any, fixture: dict[str, Any]) -> None:
        written = {
            (preset.id, preset.name, preset.scope_type, preset.auto_assign, False)
            for preset in migration._PRESETS
        }
        seeded = {
            (row["id"], row["name"], row["scope_type"], row["auto_assign"], row["deleted"])
            for row in fixture["role_presets"]
        }
        assert written == seeded

    def test_preset_permissions(self, migration: Any, fixture: dict[str, Any]) -> None:
        written = {
            (
                migration._identify("role_permission_preset", preset.id, entity_type, str(bit)),
                preset.id,
                entity_type,
                bit,
            )
            for preset in migration._PRESETS
            for entity_type, bits in preset.grants
            for bit in bits
        }
        seeded = {
            (row["id"], row["role_preset_id"], row["entity_type"], row["permission"])
            for row in fixture["role_permission_presets"]
        }
        assert written == seeded

    def test_role_permissions(self, migration: Any, fixture: dict[str, Any]) -> None:
        by_preset = {preset.id: preset for preset in migration._PRESETS}
        written = {
            (
                migration._identify("permission", role["id"], entity_type, str(bit)),
                role["id"],
                entity_type,
                bit,
            )
            for role in fixture["roles"]
            for entity_type, bits in by_preset[role["role_preset_id"]].grants
            for bit in bits
        }
        seeded = {
            (row["id"], row["role_id"], row["entity_type"], row["permission"])
            for row in fixture["permissions"]
        }
        assert written == seeded

    def test_every_role_names_a_declared_preset(
        self, migration: Any, fixture: dict[str, Any]
    ) -> None:
        declared = {preset.id for preset in migration._PRESETS}
        assert {role["role_preset_id"] for role in fixture["roles"]} <= declared
