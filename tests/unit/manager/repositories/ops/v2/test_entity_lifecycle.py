"""The entity family of the v2 write specs runs against a real database.

What these tests pin down:

- Every entity doubles as a scope: a create provisions the row's virtual scope
  node (self membership and self binding) and joins each ``member_of`` scope;
  a purge tears the same things down symmetrically; an upsert keeps the scope
  provisioned idempotently.
- The plain path never touches roles, even when matching presets exist — the
  role-managed path (typed against the combined spec) is what provisions the
  roles the scope type's active presets call for. A preset without a name
  template yields a generated per-scope role name; a template renders from the
  spec-declared ``template_value``.
- Scope types outside the RBAC element enum are accepted — the chain is open;
  only permission-carrying paths need the conversion, and teardown skips it.
- A ``member_of`` target without a virtual scope fails the whole write with
  nothing persisted; the bulk create is all-or-nothing; the bulk purge answers
  per named entity.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator, Collection, Sequence
from dataclasses import dataclass
from typing import Any, override
from uuid import UUID

import pytest
import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from ai.backend.common.data.entity.domain import DOMAIN_SCOPE_TYPE
from ai.backend.common.data.entity.project import PROJECT_SCOPE_TYPE
from ai.backend.common.data.entity.types import EntityType, ScopeRef, ScopeType
from ai.backend.common.identifier.scope import ScopeID
from ai.backend.manager.data.permission.scope_template import ScopeTemplateValue
from ai.backend.manager.data.permission.status import RoleStatus
from ai.backend.manager.data.permission.types import (
    EntityType as LegacyEntityType,
)
from ai.backend.manager.data.permission.types import (
    OperationType,
    RoleSource,
)
from ai.backend.manager.data.permission.types import (
    ScopeType as LegacyScopeType,
)
from ai.backend.manager.errors.permission import VirtualScopeNotFound
from ai.backend.manager.errors.repository import (
    EntityNotFoundError,
    RepositoryIntegrityError,
)
from ai.backend.manager.models.base import GUID, Base
from ai.backend.manager.models.rbac_models.permission.permission import PermissionRow
from ai.backend.manager.models.rbac_models.role import RoleRow
from ai.backend.manager.models.rbac_models.role_permission_preset.row import (
    RolePermissionPresetRow,
)
from ai.backend.manager.models.rbac_models.role_preset.row import RolePresetRow
from ai.backend.manager.models.specs.creator import EntityCreator, RoleManagedEntityCreator
from ai.backend.manager.models.specs.purger import EntityPurger
from ai.backend.manager.models.specs.types import ConflictCheck, IntegrityErrorCheck
from ai.backend.manager.models.specs.upserter import EntityUpserter, RoleManagedEntityUpserter
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.virtual_scope.entity_membership import EntityMembershipRow
from ai.backend.manager.models.virtual_scope.scope_binding import ScopeBindingRow
from ai.backend.manager.models.virtual_scope.virtual_scope import VirtualScopeRow
from ai.backend.manager.repositories.ops.repository import OpsRepository
from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider
from ai.backend.testutils.db import TableOrORM, with_tables

# =============================================================================
# A test entity that becomes a "project" scope (present in every enum involved),
# optionally joining "domain" scopes as a member.
# =============================================================================


class EntityLifecycleTestRow(Base):
    __tablename__ = "test_v2_entity_lifecycle"
    __table_args__ = (
        sa.UniqueConstraint("name", name="uq_test_v2_entity_lifecycle_name"),
        {"extend_existing": True},
    )

    id: Mapped[UUID] = mapped_column(
        GUID, primary_key=True, server_default=sa.text("uuid_generate_v4()")
    )
    name: Mapped[str] = mapped_column(sa.String(64), nullable=False)
    note: Mapped[str | None] = mapped_column(sa.String(64), nullable=True)


@dataclass(frozen=True)
class _EntityData:
    id: UUID
    name: str
    note: str | None


_SCOPE_TYPE = PROJECT_SCOPE_TYPE
_PARENT_SCOPE_TYPE = DOMAIN_SCOPE_TYPE

# A scope type outside every permission-layer enum — the chain accepts it as-is.
_OPEN_SCOPE_TYPE = ScopeType(EntityType("not_an_rbac_element_type"))


@dataclass
class _Creator(EntityCreator[EntityLifecycleTestRow, _EntityData]):
    name: str
    parents: tuple[UUID, ...] = ()

    @override
    def scope_type(self) -> ScopeType:
        return _SCOPE_TYPE

    @override
    def scope_id(self, row: EntityLifecycleTestRow) -> ScopeID:
        return row.id

    @override
    def member_of(self, row: EntityLifecycleTestRow) -> Collection[ScopeRef]:
        return tuple(
            ScopeRef(scope_type=_PARENT_SCOPE_TYPE, scope_id=parent) for parent in self.parents
        )

    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def build_row(self) -> EntityLifecycleTestRow:
        return EntityLifecycleTestRow(name=self.name)

    @override
    def to_data(self, row: EntityLifecycleTestRow) -> _EntityData:
        return _EntityData(id=row.id, name=row.name, note=row.note)


@dataclass
class _OpenTypeCreator(_Creator):
    @override
    def scope_type(self) -> ScopeType:
        return _OPEN_SCOPE_TYPE


@dataclass
class _RoleManagedCreator(RoleManagedEntityCreator[EntityLifecycleTestRow, _EntityData]):
    """Duplicates the plain creator's hooks on purpose: the combined root is not
    an ``EntityCreator``, so the stubs cannot share an implementation either."""

    name: str
    parents: tuple[UUID, ...] = ()

    @override
    def scope_type(self) -> ScopeType:
        return _SCOPE_TYPE

    @override
    def scope_id(self, row: EntityLifecycleTestRow) -> ScopeID:
        return row.id

    @override
    def member_of(self, row: EntityLifecycleTestRow) -> Collection[ScopeRef]:
        return tuple(
            ScopeRef(scope_type=_PARENT_SCOPE_TYPE, scope_id=parent) for parent in self.parents
        )

    @override
    def template_value(self, row: EntityLifecycleTestRow) -> ScopeTemplateValue:
        return ScopeTemplateValue(id=row.id, name=row.name, type=str(_SCOPE_TYPE))

    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def build_row(self) -> EntityLifecycleTestRow:
        return EntityLifecycleTestRow(name=self.name)

    @override
    def to_data(self, row: EntityLifecycleTestRow) -> _EntityData:
        return _EntityData(id=row.id, name=row.name, note=row.note)


@dataclass
class _Purger(EntityPurger[EntityLifecycleTestRow, _EntityData]):
    target: UUID

    @override
    def scope_of(self) -> ScopeRef:
        return ScopeRef(scope_type=_SCOPE_TYPE, scope_id=self.target)

    @override
    def row_class(self) -> type[EntityLifecycleTestRow]:
        return EntityLifecycleTestRow

    @override
    def pk_value(self) -> UUID:
        return self.target

    @override
    def conflict_checks(self) -> Sequence[ConflictCheck]:
        return ()

    @override
    def to_data(self, row: EntityLifecycleTestRow) -> _EntityData:
        return _EntityData(id=row.id, name=row.name, note=row.note)


@dataclass
class _OpenTypePurger(_Purger):
    @override
    def scope_of(self) -> ScopeRef:
        return ScopeRef(scope_type=_OPEN_SCOPE_TYPE, scope_id=self.target)


@dataclass
class _Upserter(EntityUpserter[EntityLifecycleTestRow, _EntityData]):
    name: str
    note: str | None = None
    parents: tuple[UUID, ...] = ()

    @override
    def scope_type(self) -> ScopeType:
        return _SCOPE_TYPE

    @override
    def scope_id(self, row: EntityLifecycleTestRow) -> ScopeID:
        return row.id

    @override
    def member_of(self, row: EntityLifecycleTestRow) -> Collection[ScopeRef]:
        return tuple(
            ScopeRef(scope_type=_PARENT_SCOPE_TYPE, scope_id=parent) for parent in self.parents
        )

    @override
    def row_class(self) -> type[EntityLifecycleTestRow]:
        return EntityLifecycleTestRow

    @override
    def index_elements(self) -> list[str]:
        return ["name"]

    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def build_insert_values(self) -> dict[str, Any]:
        return {"name": self.name, "note": self.note}

    @override
    def build_update_values(self) -> dict[str, Any]:
        return {"note": self.note}

    @override
    def to_data(self, row: EntityLifecycleTestRow) -> _EntityData:
        return _EntityData(id=row.id, name=row.name, note=row.note)


@dataclass
class _RoleManagedUpserter(RoleManagedEntityUpserter[EntityLifecycleTestRow, _EntityData]):
    """Duplicates the plain upserter's hooks on purpose, like the creator stub."""

    name: str
    note: str | None = None
    parents: tuple[UUID, ...] = ()

    @override
    def scope_type(self) -> ScopeType:
        return _SCOPE_TYPE

    @override
    def scope_id(self, row: EntityLifecycleTestRow) -> ScopeID:
        return row.id

    @override
    def member_of(self, row: EntityLifecycleTestRow) -> Collection[ScopeRef]:
        return tuple(
            ScopeRef(scope_type=_PARENT_SCOPE_TYPE, scope_id=parent) for parent in self.parents
        )

    @override
    def template_value(self, row: EntityLifecycleTestRow) -> ScopeTemplateValue:
        return ScopeTemplateValue(id=row.id, name=row.name, type=str(_SCOPE_TYPE))

    @override
    def row_class(self) -> type[EntityLifecycleTestRow]:
        return EntityLifecycleTestRow

    @override
    def index_elements(self) -> list[str]:
        return ["name"]

    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def build_insert_values(self) -> dict[str, Any]:
        return {"name": self.name, "note": self.note}

    @override
    def build_update_values(self) -> dict[str, Any]:
        return {"note": self.note}

    @override
    def to_data(self, row: EntityLifecycleTestRow) -> _EntityData:
        return _EntityData(id=row.id, name=row.name, note=row.note)


# =============================================================================
# Fixtures and probes
# =============================================================================

_TABLES: Sequence[TableOrORM] = [
    EntityLifecycleTestRow,
    VirtualScopeRow,
    EntityMembershipRow,
    ScopeBindingRow,
    RoleRow,
    PermissionRow,
    RolePresetRow,
    RolePermissionPresetRow,
]

_PRESET_NAME = "preset-project-member"


@pytest.fixture
async def database(
    database_connection: ExtendedAsyncSAEngine,
) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
    async with with_tables(database_connection, _TABLES):
        yield database_connection


@pytest.fixture
def repository(database: ExtendedAsyncSAEngine) -> OpsRepository[_EntityData]:
    return OpsRepository(V2DBOpsProvider(database))


@pytest.fixture
async def parent_id(database: ExtendedAsyncSAEngine) -> UUID:
    """A domain scope whose virtual scope node exists — a ``memberships`` target."""
    parent = uuid.uuid4()
    async with database.begin_session() as sess:
        sess.add(VirtualScopeRow(scope_type=_PARENT_SCOPE_TYPE, scope_id=parent))
    return parent


async def _add_presets(database: ExtendedAsyncSAEngine) -> None:
    """Two active project-scope presets: a template-less auto-assigned one carrying
    a vfolder-read permission (the member-grade convention), and a templated one
    that is not auto-assigned."""
    async with database.begin_session() as sess:
        preset_row = RolePresetRow(
            name=_PRESET_NAME,
            scope_type=LegacyScopeType.PROJECT,
            auto_assign=True,
            deleted=False,
        )
        sess.add(preset_row)
        await sess.flush()
        sess.add(
            RolePermissionPresetRow(
                role_preset_id=preset_row.id,
                entity_type=LegacyEntityType.VFOLDER,
                operation=OperationType.READ,
            )
        )
        sess.add(
            RolePresetRow(
                name="preset-templated",
                role_name_template="{{ scope.name }}-member",
                scope_type=LegacyScopeType.PROJECT,
                auto_assign=False,
                deleted=False,
            )
        )


@pytest.fixture
async def presets(database: ExtendedAsyncSAEngine) -> None:
    await _add_presets(database)


def _expected_preset_role_name(scope_id: UUID) -> str:
    """The generated name of a template-less preset role: preset name + scope id."""
    return f"{_PRESET_NAME}-{str(scope_id)[:8]}"


async def _virtual_scope_id(
    database: ExtendedAsyncSAEngine, scope_id: UUID, scope_type: ScopeType = _SCOPE_TYPE
) -> UUID | None:
    async with database.begin_readonly_session() as sess:
        result = await sess.execute(
            sa.select(VirtualScopeRow.id).where(
                VirtualScopeRow.scope_type == scope_type,
                VirtualScopeRow.scope_id == scope_id,
            )
        )
        return result.scalar_one_or_none()


async def _self_membership_exists(
    database: ExtendedAsyncSAEngine, scope_id: UUID, scope_type: ScopeType = _SCOPE_TYPE
) -> bool:
    async with database.begin_readonly_session() as sess:
        row = await sess.scalar(
            sa.select(EntityMembershipRow.entity_id)
            .join(VirtualScopeRow, EntityMembershipRow.virtual_scope_id == VirtualScopeRow.id)
            .where(
                VirtualScopeRow.scope_type == scope_type,
                VirtualScopeRow.scope_id == scope_id,
                EntityMembershipRow.entity_type == scope_type,
                EntityMembershipRow.entity_id == scope_id,
            )
        )
        return row is not None


async def _self_binding_exists(
    database: ExtendedAsyncSAEngine, scope_id: UUID, scope_type: ScopeType = _SCOPE_TYPE
) -> bool:
    async with database.begin_readonly_session() as sess:
        row = await sess.scalar(
            sa.select(ScopeBindingRow.scope_id)
            .join(VirtualScopeRow, ScopeBindingRow.virtual_scope_id == VirtualScopeRow.id)
            .where(
                VirtualScopeRow.scope_type == scope_type,
                VirtualScopeRow.scope_id == scope_id,
                ScopeBindingRow.scope_type == scope_type,
                ScopeBindingRow.scope_id == scope_id,
            )
        )
        return row is not None


async def _parent_membership_entity_ids(
    database: ExtendedAsyncSAEngine, parent_id: UUID
) -> set[UUID]:
    """Entity ids enrolled in the parent scope's virtual scope."""
    async with database.begin_readonly_session() as sess:
        rows = await sess.scalars(
            sa.select(EntityMembershipRow.entity_id)
            .join(VirtualScopeRow, EntityMembershipRow.virtual_scope_id == VirtualScopeRow.id)
            .where(
                VirtualScopeRow.scope_type == _PARENT_SCOPE_TYPE,
                VirtualScopeRow.scope_id == parent_id,
                EntityMembershipRow.entity_type == _SCOPE_TYPE,
            )
        )
        return set(rows.all())


async def _parent_binding_exists(
    database: ExtendedAsyncSAEngine, scope_id: UUID, parent_id: UUID
) -> bool:
    """Whether the parent scope is bound into the new entity's virtual scope."""
    async with database.begin_readonly_session() as sess:
        row = await sess.scalar(
            sa.select(ScopeBindingRow.scope_id)
            .join(VirtualScopeRow, ScopeBindingRow.virtual_scope_id == VirtualScopeRow.id)
            .where(
                VirtualScopeRow.scope_type == _SCOPE_TYPE,
                VirtualScopeRow.scope_id == scope_id,
                ScopeBindingRow.scope_type == _PARENT_SCOPE_TYPE,
                ScopeBindingRow.scope_id == parent_id,
            )
        )
        return row is not None


@dataclass(frozen=True)
class _RoleProbe:
    id: UUID
    source: RoleSource
    status: RoleStatus
    auto_assign: bool


async def _scope_roles(database: ExtendedAsyncSAEngine, scope_id: UUID) -> dict[str, _RoleProbe]:
    """The roles enrolled in the scope's virtual scope, by name."""
    async with database.begin_readonly_session() as sess:
        rows = (
            await sess.execute(
                sa.select(
                    RoleRow.name, RoleRow.id, RoleRow.source, RoleRow.status, RoleRow.auto_assign
                )
                .join(EntityMembershipRow, EntityMembershipRow.entity_id == RoleRow.id)
                .join(
                    VirtualScopeRow,
                    EntityMembershipRow.virtual_scope_id == VirtualScopeRow.id,
                )
                .where(
                    VirtualScopeRow.scope_type == _SCOPE_TYPE,
                    VirtualScopeRow.scope_id == scope_id,
                    EntityMembershipRow.entity_type == EntityType("role"),
                )
            )
        ).all()
        return {
            row.name: _RoleProbe(
                id=row.id, source=row.source, status=row.status, auto_assign=row.auto_assign
            )
            for row in rows
        }


async def _role_permissions(database: ExtendedAsyncSAEngine, role_id: UUID) -> set[OperationType]:
    async with database.begin_readonly_session() as sess:
        rows = await sess.scalars(
            sa.select(PermissionRow.operation).where(PermissionRow.role_id == role_id)
        )
        return set(rows.all())


async def _row_count(database: ExtendedAsyncSAEngine) -> int:
    async with database.begin_readonly_session() as sess:
        count = await sess.scalar(sa.select(sa.func.count()).select_from(EntityLifecycleTestRow))
        return count or 0


# =============================================================================
# Create (plain): every entity doubles as a scope; no roles on this path
# =============================================================================


class TestEntityCreate:
    async def test_create_provisions_virtual_scope_with_self_edges(
        self, database: ExtendedAsyncSAEngine, repository: OpsRepository[_EntityData]
    ) -> None:
        data = await repository.create_entity(_Creator(name="a"))

        assert await _virtual_scope_id(database, data.id) is not None
        assert await _self_membership_exists(database, data.id)
        assert await _self_binding_exists(database, data.id)

    async def test_create_joins_each_declared_membership(
        self,
        database: ExtendedAsyncSAEngine,
        repository: OpsRepository[_EntityData],
        parent_id: UUID,
    ) -> None:
        data = await repository.create_entity(_Creator(name="a", parents=(parent_id,)))

        assert await _parent_membership_entity_ids(database, parent_id) == {data.id}
        assert await _parent_binding_exists(database, data.id, parent_id)

    async def test_missing_membership_target_fails_without_inserting(
        self, database: ExtendedAsyncSAEngine, repository: OpsRepository[_EntityData]
    ) -> None:
        with pytest.raises(VirtualScopeNotFound):
            await repository.create_entity(_Creator(name="a", parents=(uuid.uuid4(),)))

        assert await _row_count(database) == 0
        async with database.begin_readonly_session() as sess:
            assert (await sess.scalar(sa.select(sa.func.count()).select_from(VirtualScopeRow))) == 0

    async def test_create_never_consults_presets(
        self,
        database: ExtendedAsyncSAEngine,
        repository: OpsRepository[_EntityData],
        presets: None,
    ) -> None:
        # The typed path decides role provisioning, not the preset data.
        data = await repository.create_entity(_Creator(name="a"))

        assert await _scope_roles(database, data.id) == {}

    async def test_open_scope_type_is_accepted(
        self, database: ExtendedAsyncSAEngine, repository: OpsRepository[_EntityData]
    ) -> None:
        # The chain constrains no scope types; permission paths convert lazily.
        data = await repository.create_entity(_OpenTypeCreator(name="a"))

        assert await _virtual_scope_id(database, data.id, _OPEN_SCOPE_TYPE) is not None
        assert await _self_membership_exists(database, data.id, _OPEN_SCOPE_TYPE)

    async def test_bulk_create_provisions_and_joins_each_entity(
        self,
        database: ExtendedAsyncSAEngine,
        repository: OpsRepository[_EntityData],
        parent_id: UUID,
    ) -> None:
        created = await repository.bulk_create_entities([
            _Creator(name="a", parents=(parent_id,)),
            _Creator(name="b", parents=(parent_id,)),
        ])

        assert len(created) == 2
        for data in created:
            assert await _virtual_scope_id(database, data.id) is not None
            assert await _self_membership_exists(database, data.id)
        assert await _parent_membership_entity_ids(database, parent_id) == {c.id for c in created}

    async def test_bulk_create_is_all_or_nothing(
        self, database: ExtendedAsyncSAEngine, repository: OpsRepository[_EntityData]
    ) -> None:
        with pytest.raises(RepositoryIntegrityError):
            await repository.bulk_create_entities([
                _Creator(name="dup"),
                _Creator(name="dup"),
            ])

        assert await _row_count(database) == 0


# =============================================================================
# Create (role-managed): the combined spec additionally provisions preset roles
# =============================================================================


class TestRoleManagedEntityCreate:
    async def test_create_provisions_preset_roles_with_generated_names(
        self,
        database: ExtendedAsyncSAEngine,
        repository: OpsRepository[_EntityData],
        presets: None,
    ) -> None:
        data = await repository.create_role_managed_entity(_RoleManagedCreator(name="a"))

        roles = await _scope_roles(database, data.id)
        role = roles[_expected_preset_role_name(data.id)]
        assert role.source == RoleSource.SYSTEM
        assert role.status == RoleStatus.ACTIVE
        assert role.auto_assign is True
        assert await _role_permissions(database, role.id) == {OperationType.READ}

    async def test_create_renders_templated_preset_role_names(
        self,
        database: ExtendedAsyncSAEngine,
        repository: OpsRepository[_EntityData],
        presets: None,
    ) -> None:
        # The template sees the spec-declared values, with no row lookup.
        data = await repository.create_role_managed_entity(_RoleManagedCreator(name="alpha"))

        roles = await _scope_roles(database, data.id)
        assert "alpha-member" in roles
        assert roles["alpha-member"].auto_assign is False

    async def test_create_truncates_an_over_long_templated_role_name(
        self,
        database: ExtendedAsyncSAEngine,
        repository: OpsRepository[_EntityData],
        presets: None,
    ) -> None:
        # A valid render past the column limit keeps the template's intent,
        # truncated — it does not fall back to the generic name.
        long_name = "a" * 60
        data = await repository.create_role_managed_entity(_RoleManagedCreator(name=long_name))

        roles = await _scope_roles(database, data.id)
        assert f"{long_name}-member"[:64] in roles

    async def test_create_without_presets_provisions_no_roles(
        self, database: ExtendedAsyncSAEngine, repository: OpsRepository[_EntityData]
    ) -> None:
        # The spec declares no roles, so presets are the only source of them.
        data = await repository.create_role_managed_entity(_RoleManagedCreator(name="a"))

        assert await _scope_roles(database, data.id) == {}

    async def test_bulk_create_provisions_roles_for_each_scope(
        self,
        database: ExtendedAsyncSAEngine,
        repository: OpsRepository[_EntityData],
        presets: None,
    ) -> None:
        created = await repository.bulk_create_role_managed_entities([
            _RoleManagedCreator(name="a"),
            _RoleManagedCreator(name="b"),
        ])

        for data in created:
            roles = await _scope_roles(database, data.id)
            assert _expected_preset_role_name(data.id) in roles


# =============================================================================
# Purge: the teardown mirrors the create
# =============================================================================


class TestEntityPurge:
    async def test_purge_removes_row_scope_node_and_rbac_entries(
        self,
        database: ExtendedAsyncSAEngine,
        repository: OpsRepository[_EntityData],
        presets: None,
    ) -> None:
        data = await repository.create_role_managed_entity(_RoleManagedCreator(name="a"))
        role = (await _scope_roles(database, data.id))[_expected_preset_role_name(data.id)]

        purged = await repository.purge_entity(_Purger(target=data.id))

        assert purged.id == data.id
        assert await _row_count(database) == 0
        assert await _virtual_scope_id(database, data.id) is None
        assert await _self_membership_exists(database, data.id) is False
        assert await _self_binding_exists(database, data.id) is False
        assert await _scope_roles(database, data.id) == {}
        assert await _role_permissions(database, role.id) == set()

    async def test_purge_removes_edges_in_joined_scopes(
        self,
        database: ExtendedAsyncSAEngine,
        repository: OpsRepository[_EntityData],
        parent_id: UUID,
    ) -> None:
        data = await repository.create_entity(_Creator(name="a", parents=(parent_id,)))

        await repository.purge_entity(_Purger(target=data.id))

        assert await _parent_membership_entity_ids(database, parent_id) == set()

    async def test_purge_of_a_missing_row_raises(
        self, repository: OpsRepository[_EntityData]
    ) -> None:
        with pytest.raises(EntityNotFoundError):
            await repository.purge_entity(_Purger(target=uuid.uuid4()))

    async def test_purge_of_an_open_scope_type_tears_the_node_down(
        self, database: ExtendedAsyncSAEngine, repository: OpsRepository[_EntityData]
    ) -> None:
        # No RBAC conversion exists for the type; the teardown skips permissions
        # (none can have been granted) and still removes the chain rows.
        data = await repository.create_entity(_OpenTypeCreator(name="a"))

        await repository.purge_entity(_OpenTypePurger(target=data.id))

        assert await _row_count(database) == 0
        assert await _virtual_scope_id(database, data.id, _OPEN_SCOPE_TYPE) is None

    async def test_bulk_purge_answers_for_each_named_entity(
        self, database: ExtendedAsyncSAEngine, repository: OpsRepository[_EntityData]
    ) -> None:
        data = await repository.create_entity(_Creator(name="a"))
        absent = uuid.uuid4()

        result = await repository.bulk_purge_entities({
            data.id: _Purger(target=data.id),
            absent: _Purger(target=absent),
        })

        assert set(result.successes) == {data.id}
        assert isinstance(result.errors[absent], EntityNotFoundError)
        assert await _virtual_scope_id(database, data.id) is None
        assert await _row_count(database) == 0


# =============================================================================
# Upsert: the scope stays provisioned idempotently
# =============================================================================


class TestEntityUpsert:
    async def test_upsert_insert_provisions_scope_and_memberships(
        self,
        database: ExtendedAsyncSAEngine,
        repository: OpsRepository[_EntityData],
        parent_id: UUID,
    ) -> None:
        data = await repository.upsert_entity(_Upserter(name="a", parents=(parent_id,)))

        assert await _virtual_scope_id(database, data.id) is not None
        assert await _self_membership_exists(database, data.id)
        assert await _parent_membership_entity_ids(database, parent_id) == {data.id}

    async def test_upsert_update_keeps_registration_single(
        self,
        database: ExtendedAsyncSAEngine,
        repository: OpsRepository[_EntityData],
        parent_id: UUID,
    ) -> None:
        first = await repository.upsert_entity(_Upserter(name="a", parents=(parent_id,)))
        second = await repository.upsert_entity(
            _Upserter(name="a", note="updated", parents=(parent_id,))
        )

        assert second.id == first.id
        assert second.note == "updated"
        assert await _row_count(database) == 1
        assert await _parent_membership_entity_ids(database, parent_id) == {first.id}

    async def test_upsert_with_a_missing_membership_target_fails(
        self, database: ExtendedAsyncSAEngine, repository: OpsRepository[_EntityData]
    ) -> None:
        with pytest.raises(VirtualScopeNotFound):
            await repository.upsert_entity(_Upserter(name="a", parents=(uuid.uuid4(),)))

        assert await _row_count(database) == 0

    async def test_role_managed_upsert_insert_provisions_preset_roles(
        self,
        database: ExtendedAsyncSAEngine,
        repository: OpsRepository[_EntityData],
        presets: None,
    ) -> None:
        data = await repository.upsert_role_managed_entity(_RoleManagedUpserter(name="a"))

        roles = await _scope_roles(database, data.id)
        assert _expected_preset_role_name(data.id) in roles

    async def test_role_managed_upsert_update_does_not_duplicate_roles(
        self,
        database: ExtendedAsyncSAEngine,
        repository: OpsRepository[_EntityData],
        presets: None,
    ) -> None:
        # Roles are provisioned only when the upsert actually created the scope.
        first = await repository.upsert_role_managed_entity(_RoleManagedUpserter(name="a"))
        second = await repository.upsert_role_managed_entity(
            _RoleManagedUpserter(name="a", note="updated")
        )

        assert second.id == first.id
        roles = await _scope_roles(database, first.id)
        # One role per preset, exactly once — the update pass added none.
        assert sorted(roles) == sorted([_expected_preset_role_name(first.id), "a-member"])
