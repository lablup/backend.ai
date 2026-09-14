"""The seed role declaration answers for every kind this build knows."""

from __future__ import annotations

import json
import uuid

import pytest
from pydantic import ValidationError

from ai.backend.common.data.entity.types import EntityType
from ai.backend.common.data.permission.types import Permission
from ai.backend.manager.cli.permissions import _REPOSITORY, _TARGETS
from ai.backend.manager.cli.role_fixture import RoleFixture
from ai.backend.manager.data.permission.seed.check import RoleSeedChecker
from ai.backend.manager.data.permission.seed.kinds import PermissionKinds
from ai.backend.manager.data.permission.seed.loader import RoleSeedLoader
from ai.backend.manager.data.permission.seed.role import RoleSeed
from ai.backend.manager.errors.permission import InvalidRoleSeed
from ai.backend.manager.models.base import ensure_all_tables_registered, metadata


@pytest.fixture(scope="module")
def kinds() -> PermissionKinds:
    return PermissionKinds()


@pytest.fixture(scope="module")
def seeds() -> list[RoleSeed]:
    return RoleSeedLoader().load()


def _entity_type_subclasses() -> list[type[EntityType]]:
    found: list[type[EntityType]] = []
    pending = list(EntityType.__subclasses__())
    while pending:
        kind = pending.pop()
        found.append(kind)
        pending.extend(kind.__subclasses__())
    return found


def _empty(kinds: PermissionKinds) -> dict[str, list[str]]:
    return {kind: [] for kind in kinds.declared()}


def _seed(name: str, permissions: dict[str, list[str]]) -> RoleSeed:
    return RoleSeed.model_validate({
        "id": str(uuid.uuid5(uuid.NAMESPACE_DNS, name)),
        "name": name,
        "scope_type": "project",
        "auto_assign": False,
        "permissions": permissions,
    })


class TestDeclaration:
    def test_every_role_states_every_kind(
        self, kinds: PermissionKinds, seeds: list[RoleSeed]
    ) -> None:
        for seed in seeds:
            assert set(seed.permissions) == kinds.declared(), seed.name

    def test_the_declaration_has_no_findings(
        self, kinds: PermissionKinds, seeds: list[RoleSeed]
    ) -> None:
        findings = RoleSeedChecker(kinds, seeds).findings()
        assert findings == [], [finding.render() for finding in findings]

    def test_role_names_are_unique(self, seeds: list[RoleSeed]) -> None:
        names = [seed.name for seed in seeds]
        assert len(names) == len(set(names))


class TestKindCatalog:
    """The kinds come from the entity package, and each answers for itself."""

    def test_only_the_entity_package_declares_a_kind(self, kinds: PermissionKinds) -> None:
        package = "ai.backend.common.data.entity"
        declared = {
            kind.name() for kind in _entity_type_subclasses() if kind.__module__.startswith(package)
        }
        assert kinds.declared() == declared

    def test_a_kind_without_a_name_is_refused(self) -> None:
        nameless = type("NamelessEntityType", (EntityType,), {})
        nameless.__module__ = "ai.backend.common.data.entity.nameless"
        try:
            with pytest.raises(InvalidRoleSeed, match="declares no name"):
                PermissionKinds()
        finally:
            nameless.__module__ = "tests.detached"

    def test_a_kind_without_a_description_is_refused(self) -> None:
        undescribed = type(
            "UndescribedEntityType",
            (EntityType,),
            {"name": classmethod(lambda cls: "undescribed")},
        )
        undescribed.__module__ = "ai.backend.common.data.entity.undescribed"
        try:
            with pytest.raises(InvalidRoleSeed, match="declares no description"):
                PermissionKinds()
        finally:
            undescribed.__module__ = "tests.detached"


class TestOperationVocabulary:
    def test_an_empty_list_grants_nothing(self) -> None:
        seed = _seed("member", {"session": []})
        assert seed.permissions["session"] is Permission.NONE
        assert seed.granted() == {}

    def test_names_become_bits(self) -> None:
        seed = _seed("admin", {"session": ["read", "hard_delete"]})
        assert seed.permissions["session"] == Permission.READ | Permission.HARD_DELETE

    def test_an_unknown_operation_is_refused(self) -> None:
        with pytest.raises(ValidationError, match="soft-delete"):
            _seed("admin", {"session": ["soft-delete"]})

    def test_a_repeated_operation_is_refused(self) -> None:
        with pytest.raises(ValidationError, match="stated twice"):
            _seed("admin", {"session": ["read", "read"]})

    def test_an_unknown_header_field_is_refused(self) -> None:
        with pytest.raises(ValidationError):
            RoleSeed.model_validate({
                "id": str(uuid.uuid4()),
                "name": "admin",
                "scope_type": "project",
                "auto_assign": False,
                "permissions": {},
                "role_name_template": "role_{name}",
            })


class TestChecker:
    def test_a_missing_kind_is_reported(self, kinds: PermissionKinds) -> None:
        findings = RoleSeedChecker(kinds, [_seed("project_admin", {})]).findings()
        assert any("is not stated" in finding.message for finding in findings)

    def test_an_unknown_kind_is_reported(self, kinds: PermissionKinds) -> None:
        stated = _empty(kinds)
        stated["nowhere"] = []
        findings = RoleSeedChecker(kinds, [_seed("project_admin", stated)]).findings()
        assert any("is not an entity type" in f.message for f in findings)

    def test_a_field_type_is_not_an_entity_type(self, kinds: PermissionKinds) -> None:
        stated = _empty(kinds)
        stated["keypair"] = ["read"]
        findings = RoleSeedChecker(kinds, [_seed("project_admin", stated)]).findings()
        assert any("keypair is not an entity type" in finding.message for finding in findings)

    def test_a_member_beyond_its_admin_is_reported(self, kinds: PermissionKinds) -> None:
        admin = _seed("project_admin", _empty(kinds) | {"session": ["read"]})
        member = _seed("project_member", _empty(kinds) | {"session": ["read", "update"]})
        findings = RoleSeedChecker(kinds, [admin, member]).findings()
        assert any("what project_admin does not" in finding.message for finding in findings)

    def test_two_files_stating_one_role_are_reported(self, kinds: PermissionKinds) -> None:
        seed = _seed("project_admin", _empty(kinds))
        findings = RoleSeedChecker(kinds, [seed, seed]).findings()
        assert any("2 files state this role" in finding.message for finding in findings)


class TestFixture:
    """The seed fixture is what the declaration renders, never edited by hand."""

    def test_the_written_files_are_current(self, seeds: list[RoleSeed]) -> None:
        body = json.dumps(
            RoleFixture(seeds, _REPOSITORY / "fixtures" / "manager").render(), indent=4
        )
        for target in _TARGETS:
            written = (_REPOSITORY / target).read_text(encoding="utf-8")
            assert written == body + "\n", f"{target} is stale; run `mgr permissions emit`"

    def test_rendering_twice_is_the_same(self, seeds: list[RoleSeed]) -> None:
        fixtures = _REPOSITORY / "fixtures" / "manager"
        assert RoleFixture(seeds, fixtures).render() == RoleFixture(seeds, fixtures).render()

    def test_every_permission_row_holds_one_bit(self, seeds: list[RoleSeed]) -> None:
        rendered = RoleFixture(seeds, _REPOSITORY / "fixtures" / "manager").render()
        for row in rendered["permissions"]:
            bit = row["permission"]
            assert bit > 0 and bit & (bit - 1) == 0

    def test_every_role_is_reachable_from_a_preset(self, seeds: list[RoleSeed]) -> None:
        rendered = RoleFixture(seeds, _REPOSITORY / "fixtures" / "manager").render()
        role_ids = {role["id"] for role in rendered["roles"]}
        assert {row["role_id"] for row in rendered["permissions"]} <= role_ids
        assert {row["role_id"] for row in rendered["user_roles"]} <= role_ids
        assert not any(preset["deleted"] for preset in rendered["role_presets"])

    def test_every_row_fits_its_table(self, seeds: list[RoleSeed]) -> None:
        """A generated row names the columns its table has, and misses none it needs."""
        ensure_all_tables_registered()
        rendered = RoleFixture(seeds, _REPOSITORY / "fixtures" / "manager").render()
        for name, rows in rendered.items():
            if name.startswith("__"):
                continue
            table = metadata.tables.get(name)
            assert table is not None, f"{name} is not a table"
            columns = {column.name for column in table.columns}
            needed = {
                column.name
                for column in table.columns
                if not column.nullable and column.default is None and column.server_default is None
            }
            for row in rows:
                assert not set(row) - columns, f"{name}: {sorted(set(row) - columns)}"
                assert not needed - set(row), f"{name}: {sorted(needed - set(row))}"

    def test_a_preset_carries_the_id_its_file_states(self, seeds: list[RoleSeed]) -> None:
        rendered = RoleFixture(seeds, _REPOSITORY / "fixtures" / "manager").render()
        declared = {str(seed.id) for seed in seeds}
        assert {preset["id"] for preset in rendered["role_presets"]} == declared
        assert {role["role_preset_id"] for role in rendered["roles"]} <= declared

    def test_a_derived_id_is_a_uuid7(self, seeds: list[RoleSeed]) -> None:
        """Only the stated preset ids keep the version they were minted with."""
        rendered = RoleFixture(seeds, _REPOSITORY / "fixtures" / "manager").render()
        for name in ("roles", "user_roles", "permissions", "virtual_entities"):
            for row in rendered[name]:
                assert uuid.UUID(row["id"]).version == 7, f"{name}: {row['id']}"
