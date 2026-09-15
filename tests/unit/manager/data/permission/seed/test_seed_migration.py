"""The migration writes the rows the fixture holds, down to the id.

A database seeded from the fixture and one carried here by the migration have to end
up the same, or the seed says one thing and a running system another.
"""

from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any

import pytest
from alembic.util.pyfiles import load_python_file

_REVISION = "f4a1c9d20b73_sync_seed_roles_with_their_declaration"
_USER_OWNER_REVISION = "dc61fa027fc1_assign_every_user_their_user_owner_role"
_REPOSITORY = Path(__file__).resolve().parents[6]
_VERSIONS = _REPOSITORY / "src/ai/backend/manager/models/alembic/versions"


@pytest.fixture(scope="module")
def migration() -> Any:
    """The revision, imported by path: `versions/` is not a package."""
    return load_python_file(str(_VERSIONS), f"{_REVISION}.py")


@pytest.fixture(scope="module")
def user_owner_migration() -> Any:
    return load_python_file(str(_VERSIONS), f"{_USER_OWNER_REVISION}.py")


@pytest.fixture(scope="module")
def fixture() -> dict[str, Any]:
    base = _REPOSITORY / "fixtures/manager"
    loaded: dict[str, Any] = {}
    for name in ("example-role-presets.json", "example-roles.json"):
        loaded.update(json.loads((base / name).read_text(encoding="utf-8")))
    return loaded


class TestMigrationMatchesFixture:
    def test_presets(
        self, migration: Any, user_owner_migration: Any, fixture: dict[str, Any]
    ) -> None:
        # The user_owner revision turns that preset's auto_assign on afterwards.
        written = {
            (
                preset.id,
                preset.name,
                preset.scope_type,
                preset.auto_assign or preset.id == user_owner_migration._USER_OWNER_PRESET_ID,
                False,
            )
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
                migration._preset_for(role["scope_type"], role["scope_id"], role["name"])
                == role["role_preset_id"]
            ), role["name"]

    @pytest.mark.parametrize(
        ("scope_type", "name"),
        [
            ("domain", "role_superadmin"),
            ("domain", "role_monitor"),
            ("project", "a-role-someone-made"),
            ("project", "gpu-team-admin"),
            ("project", "ml_member"),
            ("domain", "billing-admin"),
            ("user", "my-custom-role"),
            ("resource_group", "role_resource_group_admin"),
        ],
    )
    def test_what_no_preset_made_maps_to_nothing(
        self, migration: Any, scope_type: str, name: str
    ) -> None:
        """A name the earlier migrations never wrote is not one of theirs, whatever it
        ends in."""
        assert migration._preset_for(scope_type, str(uuid.uuid4()), name) is None
