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
    loaded: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    return loaded


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


class TestEntityTypeSweep:
    def test_the_seed_names_only_kept_types(self, migration: Any, fixture: dict[str, Any]) -> None:
        """What the sweep keeps covers what the seed writes, or it deletes the seed."""
        named = {row["entity_type"] for row in fixture["permissions"]}
        assert named <= migration._ENTITY_TYPES

    def test_the_retired_names_are_not_kept(self, migration: Any) -> None:
        for name, replacement in migration._RETIRED.items():
            assert name not in migration._ENTITY_TYPES, name
            if replacement is not None:
                assert replacement in migration._ENTITY_TYPES, replacement


class TestPresetMapping:
    def test_every_seed_role_maps_to_the_preset_it_carries(
        self, migration: Any, fixture: dict[str, Any]
    ) -> None:
        for role in fixture["roles"]:
            assert (
                migration._preset_for(role["scope_type"], role["name"]) == role["role_preset_id"]
            ), role["name"]

    @pytest.mark.parametrize(
        ("scope_type", "name", "preset"),
        [
            ("domain", "domain-default-admin", "domain_admin"),
            ("project", "project-2de2b969-admin", "project_admin"),
            ("project", "project-2de2b969-member", "project_member"),
            ("user", "user-alice", "user_owner"),
        ],
    )
    def test_the_runtime_naming_rule_maps_too(
        self, migration: Any, scope_type: str, name: str, preset: str
    ) -> None:
        """Two naming rules are in the wild; a role made by either is still seed-owned."""
        by_id = {p.id: p.name for p in migration._PRESETS}
        assert by_id[migration._preset_for(scope_type, name)] == preset

    @pytest.mark.parametrize(
        ("scope_type", "name"),
        [
            ("domain", "role_superadmin"),
            ("domain", "role_monitor"),
            ("project", "a-role-someone-made"),
            ("resource_group", "role_resource_group_admin"),
        ],
    )
    def test_what_no_preset_made_maps_to_nothing(
        self, migration: Any, scope_type: str, name: str
    ) -> None:
        assert migration._preset_for(scope_type, name) is None
