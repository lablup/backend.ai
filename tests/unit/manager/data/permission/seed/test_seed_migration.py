"""The migration writes the presets the fixture holds, down to the id.

A database seeded from the fixture and one carried here by the migration have to hold
the same presets, or the seed says one thing and a running system another.
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
_DOMAIN_MEMBER_REVISION = "e7d2a9c41b60_assign_every_user_their_domain_member_role"
_PROJECT_MEMBER_READ_REVISION = "a0f597deb5e5_grant_project_members_read_on_their_project"
_DOMAIN_MEMBER_READ_REVISION = "c4a71e0d5b38_grant_domain_members_read_on_their_domain"
_DOMAIN_MEMBER_PRESET_REVISION = "a3f60d2b7c19_grant_domain_members_read_on_resource_presets"
_PUBLIC_MEMBER_REVISION = "c3e8a1f05b27_add_preset_scope_and_public_member_role"
_MEMBER_READS_REVISION = "a1f6b7c4d902_grant_image_and_project_reads_to_members"
_OWN_POLICY_READS_REVISION = "b8e0c1f4a276_grant_seed_roles_read_on_their_own_policy"
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
def domain_member_migration() -> Any:
    return load_python_file(str(_VERSIONS), f"{_DOMAIN_MEMBER_REVISION}.py")


@pytest.fixture(scope="module")
def project_member_read_migration() -> Any:
    return load_python_file(str(_VERSIONS), f"{_PROJECT_MEMBER_READ_REVISION}.py")


@pytest.fixture(scope="module")
def domain_member_read_migration() -> Any:
    return load_python_file(str(_VERSIONS), f"{_DOMAIN_MEMBER_READ_REVISION}.py")


@pytest.fixture(scope="module")
def domain_member_preset_migration() -> Any:
    return load_python_file(str(_VERSIONS), f"{_DOMAIN_MEMBER_PRESET_REVISION}.py")


@pytest.fixture(scope="module")
def public_member_migration() -> Any:
    return load_python_file(str(_VERSIONS), f"{_PUBLIC_MEMBER_REVISION}.py")


@pytest.fixture(scope="module")
def member_reads_migration() -> Any:
    return load_python_file(str(_VERSIONS), f"{_MEMBER_READS_REVISION}.py")


@pytest.fixture(scope="module")
def own_policy_reads_migration() -> Any:
    return load_python_file(str(_VERSIONS), f"{_OWN_POLICY_READS_REVISION}.py")


@pytest.fixture(scope="module")
def fixture() -> dict[str, Any]:
    path = _REPOSITORY / "fixtures/manager/example-role-presets.json"
    loaded: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    return loaded


class TestMigrationMatchesFixture:
    def test_presets(
        self,
        migration: Any,
        user_owner_migration: Any,
        domain_member_migration: Any,
        public_member_migration: Any,
        fixture: dict[str, Any],
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
        # The domain_member revision writes its preset afterwards.
        written.add((
            domain_member_migration._PRESET_ID,
            domain_member_migration._PRESET_NAME,
            domain_member_migration._SCOPE_TYPE,
            True,
            False,
        ))
        written.add((
            public_member_migration._PRESET_ID,
            public_member_migration._PRESET_NAME,
            public_member_migration._SCOPE_TYPE,
            True,
            False,
        ))
        seeded = {
            (row["id"], row["name"], row["scope_type"], row["auto_assign"], row["deleted"])
            for row in fixture["role_presets"]
        }
        assert written == seeded

    def test_preset_permissions(
        self,
        migration: Any,
        domain_member_migration: Any,
        domain_member_read_migration: Any,
        domain_member_preset_migration: Any,
        project_member_read_migration: Any,
        public_member_migration: Any,
        member_reads_migration: Any,
        own_policy_reads_migration: Any,
        fixture: dict[str, Any],
    ) -> None:
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
        written |= {
            (
                domain_member_migration._identify(
                    "role_permission_preset",
                    domain_member_migration._PRESET_ID,
                    entity_type,
                    str(bit),
                ),
                domain_member_migration._PRESET_ID,
                entity_type,
                bit,
            )
            for entity_type, bits in domain_member_migration._GRANTS
            for bit in bits
        }
        written |= {
            (
                public_member_migration._identify(
                    "role_permission_preset",
                    public_member_migration._PRESET_ID,
                    entity_type,
                    str(bit),
                ),
                public_member_migration._PRESET_ID,
                entity_type,
                bit,
            )
            for entity_type, bits in public_member_migration._GRANTS
            for bit in bits
        }
        written.add((
            domain_member_read_migration._identify(
                "role_permission_preset",
                domain_member_read_migration._PRESET_ID,
                domain_member_read_migration._ENTITY_TYPE,
                str(domain_member_read_migration._READ),
            ),
            domain_member_read_migration._PRESET_ID,
            domain_member_read_migration._ENTITY_TYPE,
            domain_member_read_migration._READ,
        ))
        written.add((
            domain_member_preset_migration._identify(
                "role_permission_preset",
                domain_member_preset_migration._PRESET_ID,
                domain_member_preset_migration._ENTITY_TYPE,
                str(domain_member_preset_migration._READ),
            ),
            domain_member_preset_migration._PRESET_ID,
            domain_member_preset_migration._ENTITY_TYPE,
            domain_member_preset_migration._READ,
        ))
        written.add((
            project_member_read_migration._identify(
                "role_permission_preset",
                project_member_read_migration._PRESET_ID,
                project_member_read_migration._ENTITY_TYPE,
                str(project_member_read_migration._READ),
            ),
            project_member_read_migration._PRESET_ID,
            project_member_read_migration._ENTITY_TYPE,
            project_member_read_migration._READ,
        ))
        written |= {
            (
                member_reads_migration._identify(
                    "role_permission_preset",
                    preset_id,
                    entity_type,
                    str(member_reads_migration._READ),
                ),
                preset_id,
                entity_type,
                member_reads_migration._READ,
            )
            for preset_id, entity_type in member_reads_migration._GRANTS
        }
        written |= {
            (
                own_policy_reads_migration._identify(
                    "role_permission_preset",
                    preset_id,
                    entity_type,
                    str(own_policy_reads_migration._READ),
                ),
                preset_id,
                entity_type,
                own_policy_reads_migration._READ,
            )
            for preset_id, entity_type in own_policy_reads_migration._GRANTS
        }
        seeded = {
            (row["id"], row["role_preset_id"], row["entity_type"], row["permission"])
            for row in fixture["role_permission_presets"]
        }
        assert written == seeded


class TestEntityTypeSweep:
    def test_the_seed_names_only_kept_types(self, migration: Any, fixture: dict[str, Any]) -> None:
        """What the sweep keeps covers what the presets grant, or it deletes the grants."""
        named = {row["entity_type"] for row in fixture["role_permission_presets"]}
        assert named <= migration._ENTITY_TYPES

    def test_the_retired_names_are_not_kept(self, migration: Any) -> None:
        for name, replacement in migration._RETIRED.items():
            assert name not in migration._ENTITY_TYPES, name
            if replacement is not None:
                assert replacement in migration._ENTITY_TYPES, replacement


class TestPresetMapping:
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

    @pytest.mark.parametrize(
        ("scope_type", "name", "preset_name"),
        [
            ("domain", "domain-default-admin", "domain_admin"),
            ("project", "project-{short}-admin", "project_admin"),
            ("project", "project-{short}-member", "project_member"),
            ("user", "user-{short}", "user_owner"),
        ],
    )
    def test_the_runtime_names_map_to_their_preset(
        self, migration: Any, scope_type: str, name: str, preset_name: str
    ) -> None:
        """The runtime named the roles it made before presets did."""
        scope_id = str(uuid.uuid4())
        preset_id = next(p.id for p in migration._PRESETS if p.name == preset_name)
        assert (
            migration._preset_for(scope_type, scope_id, name.format(short=scope_id[:8]))
            == preset_id
        )

    @pytest.mark.parametrize(
        ("scope_type", "name"),
        [
            ("project", "project-00000000-admin"),
            ("user", "user-00000000"),
            ("domain", "domain-default-member"),
        ],
    )
    def test_a_runtime_name_of_another_scope_maps_to_nothing(
        self, migration: Any, scope_type: str, name: str
    ) -> None:
        assert migration._preset_for(scope_type, str(uuid.uuid4()), name) is None
