"""The entity family of the v2 write specs runs against a real database.

What these tests pin down:

- Every entity doubles as a scope: a create provisions the row's virtual entity
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
- A ``member_of`` target without a virtual entity fails the whole write with
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
from sqlalchemy.orm import InstrumentedAttribute, Mapped, aliased, mapped_column

from ai.backend.common.data.entity.domain import DOMAIN_SCOPE_TYPE
from ai.backend.common.data.entity.project import PROJECT_SCOPE_TYPE
from ai.backend.common.data.entity.types import (
    EntityIdentifier,
    EntityType,
    FieldData,
    FieldIdentifier,
    FieldType,
    ScopeType,
)
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
from ai.backend.manager.errors.permission import VirtualEntityNotFound
from ai.backend.manager.errors.repository import (
    EntityNotFoundError,
    RepositoryIntegrityError,
)
from ai.backend.manager.models.base import GUID, Base
from ai.backend.manager.models.entity_label.row import EntityLabelRow
from ai.backend.manager.models.rbac_models.permission.permission import PermissionRow
from ai.backend.manager.models.rbac_models.role import RoleRow
from ai.backend.manager.models.rbac_models.role_permission_preset.row import (
    RolePermissionPresetRow,
)
from ai.backend.manager.models.rbac_models.role_preset.row import RolePresetRow
from ai.backend.manager.models.specs.creator import (
    DanglingFieldCreator,
    EntityCreator,
    RoleManagedEntityCreator,
)
from ai.backend.manager.models.specs.purger import EntityPurger
from ai.backend.manager.models.specs.types import ConflictCheck, IntegrityErrorCheck
from ai.backend.manager.models.specs.upserter import EntityUpserter
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.virtual_entity.entity_membership import EntityMembershipRow
from ai.backend.manager.models.virtual_entity.scope_binding import ScopeBindingRow
from ai.backend.manager.models.virtual_entity.virtual_entity import VirtualEntityRow
from ai.backend.manager.repositories.ops.repository import OpsRepository
from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider
from ai.backend.testutils.db import with_tables

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


class _EntityID(EntityIdentifier):
    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return EntityType(_SCOPE_TYPE)


class _ParentID(EntityIdentifier):
    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return EntityType(_PARENT_SCOPE_TYPE)


class _OpenTypeID(EntityIdentifier):
    """An id whose type is outside the RBAC element enum."""

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return EntityType(_OPEN_SCOPE_TYPE)


@dataclass
class _Creator(EntityCreator[EntityLifecycleTestRow, _EntityData]):
    name: str
    parents: tuple[UUID, ...] = ()

    @override
    def entity_id(self, row: EntityLifecycleTestRow) -> EntityIdentifier:
        return _EntityID(row.id)

    @override
    def member_of(self, row: EntityLifecycleTestRow) -> Collection[EntityIdentifier]:
        return tuple(_ParentID(parent) for parent in self.parents)

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
    def entity_id(self, row: EntityLifecycleTestRow) -> EntityIdentifier:
        return _OpenTypeID(row.id)


@dataclass
class _RoleManagedCreator(RoleManagedEntityCreator[EntityLifecycleTestRow, _EntityData]):
    """Duplicates the plain creator's hooks on purpose: the combined root is not
    an ``EntityCreator``, so the stubs cannot share an implementation either."""

    name: str
    parents: tuple[UUID, ...] = ()

    @override
    def entity_id(self, row: EntityLifecycleTestRow) -> EntityIdentifier:
        return _EntityID(row.id)

    @override
    def member_of(self, row: EntityLifecycleTestRow) -> Collection[EntityIdentifier]:
        return tuple(_ParentID(parent) for parent in self.parents)

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


class _TestEntityID(EntityIdentifier):
    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return EntityType(_SCOPE_TYPE)


class _OpenTypeEntityID(EntityIdentifier):
    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return EntityType(_OPEN_SCOPE_TYPE)


@dataclass
class _Purger(EntityPurger[EntityLifecycleTestRow, _EntityData]):
    target: UUID

    @override
    def entity_id(self) -> EntityIdentifier:
        return _TestEntityID(self.target)

    @override
    def row_class(self) -> type[EntityLifecycleTestRow]:
        return EntityLifecycleTestRow

    @override
    def target_id_column(self) -> InstrumentedAttribute[Any]:
        return EntityLifecycleTestRow.id

    @override
    def conflict_checks(self) -> Sequence[ConflictCheck]:
        return ()

    @override
    def to_data(self, row: EntityLifecycleTestRow) -> _EntityData:
        return _EntityData(id=row.id, name=row.name, note=row.note)


@dataclass
class _OpenTypePurger(_Purger):
    @override
    def entity_id(self) -> EntityIdentifier:
        return _OpenTypeEntityID(self.target)


@dataclass
class _Upserter(EntityUpserter[EntityLifecycleTestRow, _EntityData]):
    name: str
    note: str | None = None
    parents: tuple[UUID, ...] = ()

    @override
    def entity_id(self, row: EntityLifecycleTestRow) -> EntityIdentifier:
        return _EntityID(row.id)

    @override
    def member_of(self, row: EntityLifecycleTestRow) -> Collection[EntityIdentifier]:
        return tuple(_ParentID(parent) for parent in self.parents)

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


@pytest.fixture
async def database(
    database_connection: ExtendedAsyncSAEngine,
) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
    async with with_tables(
        database_connection,
        [
            VirtualEntityRow,
            EntityMembershipRow,
            ScopeBindingRow,
            EntityLabelRow,
            RolePresetRow,
            RolePermissionPresetRow,
            RoleRow,
            PermissionRow,
            EntityLifecycleTestRow,
        ],
    ):
        yield database_connection


@pytest.fixture
def repository(database: ExtendedAsyncSAEngine) -> OpsRepository[_EntityData]:
    return OpsRepository(V2DBOpsProvider(database))


_PRESET_NAME = "preset-project-member"


@pytest.fixture
async def parent_id(database: ExtendedAsyncSAEngine) -> UUID:
    """A domain scope whose virtual entity node exists — a ``memberships`` target."""
    parent = uuid.uuid4()
    async with database.begin_session() as sess:
        sess.add(VirtualEntityRow(entity_type=_PARENT_SCOPE_TYPE, entity_id=parent))
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


async def _virtual_entity_id(
    database: ExtendedAsyncSAEngine, scope_id: UUID, scope_type: ScopeType = _SCOPE_TYPE
) -> UUID | None:
    async with database.begin_readonly_session() as sess:
        result = await sess.execute(
            sa.select(VirtualEntityRow.id).where(
                VirtualEntityRow.entity_type == scope_type,
                VirtualEntityRow.entity_id == scope_id,
            )
        )
        return result.scalar_one_or_none()


def _node_id(scope_type: ScopeType, scope_id: UUID) -> sa.ScalarSelect[Any]:
    return (
        sa.select(VirtualEntityRow.id)
        .where(
            VirtualEntityRow.entity_type == scope_type,
            VirtualEntityRow.entity_id == scope_id,
        )
        .scalar_subquery()
    )


async def _self_membership_exists(
    database: ExtendedAsyncSAEngine, scope_id: UUID, scope_type: ScopeType = _SCOPE_TYPE
) -> bool:
    async with database.begin_readonly_session() as sess:
        node = _node_id(scope_type, scope_id)
        row = await sess.scalar(
            sa.select(EntityMembershipRow.member_entity_id).where(
                EntityMembershipRow.virtual_entity_id == node,
                EntityMembershipRow.member_entity_id == node,
            )
        )
        return row is not None


async def _self_binding_exists(
    database: ExtendedAsyncSAEngine, scope_id: UUID, scope_type: ScopeType = _SCOPE_TYPE
) -> bool:
    async with database.begin_readonly_session() as sess:
        node = _node_id(scope_type, scope_id)
        row = await sess.scalar(
            sa.select(ScopeBindingRow.scope_entity_id).where(
                ScopeBindingRow.virtual_entity_id == node,
                ScopeBindingRow.scope_entity_id == node,
            )
        )
        return row is not None


async def _parent_membership_entity_ids(
    database: ExtendedAsyncSAEngine, parent_id: UUID
) -> set[UUID]:
    """Entity ids enrolled in the parent scope's virtual entity."""
    member = aliased(VirtualEntityRow)
    async with database.begin_readonly_session() as sess:
        rows = await sess.scalars(
            sa.select(member.entity_id)
            .join(EntityMembershipRow, EntityMembershipRow.member_entity_id == member.id)
            .where(
                EntityMembershipRow.virtual_entity_id == _node_id(_PARENT_SCOPE_TYPE, parent_id),
                member.entity_type == _SCOPE_TYPE,
            )
        )
        return set(rows.all())


async def _parent_binding_exists(
    database: ExtendedAsyncSAEngine, scope_id: UUID, parent_id: UUID
) -> bool:
    """Whether the parent scope is bound into the new entity's virtual entity."""
    async with database.begin_readonly_session() as sess:
        row = await sess.scalar(
            sa.select(ScopeBindingRow.scope_entity_id).where(
                ScopeBindingRow.virtual_entity_id == _node_id(_SCOPE_TYPE, scope_id),
                ScopeBindingRow.scope_entity_id == _node_id(_PARENT_SCOPE_TYPE, parent_id),
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
    """The roles enrolled in the scope's virtual entity, by name."""
    role_node = aliased(VirtualEntityRow)
    async with database.begin_readonly_session() as sess:
        rows = (
            await sess.execute(
                sa.select(
                    RoleRow.name, RoleRow.id, RoleRow.source, RoleRow.status, RoleRow.auto_assign
                )
                .join(role_node, role_node.entity_id == RoleRow.id)
                .join(EntityMembershipRow, EntityMembershipRow.member_entity_id == role_node.id)
                .where(
                    EntityMembershipRow.virtual_entity_id == _node_id(_SCOPE_TYPE, scope_id),
                    role_node.entity_type == EntityType("role"),
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
            sa.select(PermissionRow.permission).where(PermissionRow.role_id == role_id)
        )
        return {permission.to_operation() for permission in rows.all()}


async def _row_count(database: ExtendedAsyncSAEngine) -> int:
    async with database.begin_readonly_session() as sess:
        count = await sess.scalar(sa.select(sa.func.count()).select_from(EntityLifecycleTestRow))
        return count or 0


# =============================================================================
# Create (plain): every entity doubles as a scope; no roles on this path
# =============================================================================


class TestEntityCreate:
    async def test_create_provisions_virtual_entity_with_self_edges(
        self, database: ExtendedAsyncSAEngine, repository: OpsRepository[_EntityData]
    ) -> None:
        data = await repository.create_entity(_Creator(name="a"))

        assert await _virtual_entity_id(database, data.id) is not None
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
        with pytest.raises(VirtualEntityNotFound):
            await repository.create_entity(_Creator(name="a", parents=(uuid.uuid4(),)))

        assert await _row_count(database) == 0
        async with database.begin_readonly_session() as sess:
            assert (
                await sess.scalar(sa.select(sa.func.count()).select_from(VirtualEntityRow))
            ) == 0

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

        assert await _virtual_entity_id(database, data.id, _OPEN_SCOPE_TYPE) is not None
        assert await _self_membership_exists(database, data.id, _OPEN_SCOPE_TYPE)

    async def test_bulk_create_provisions_and_joins_each_entity(
        self,
        database: ExtendedAsyncSAEngine,
        repository: OpsRepository[_EntityData],
        parent_id: UUID,
    ) -> None:
        created = await repository.atomic_create_entities([
            _Creator(name="a", parents=(parent_id,)),
            _Creator(name="b", parents=(parent_id,)),
        ])

        assert len(created) == 2
        for data in created:
            assert await _virtual_entity_id(database, data.id) is not None
            assert await _self_membership_exists(database, data.id)
        assert await _parent_membership_entity_ids(database, parent_id) == {c.id for c in created}

    async def test_bulk_create_is_all_or_nothing(
        self, database: ExtendedAsyncSAEngine, repository: OpsRepository[_EntityData]
    ) -> None:
        with pytest.raises(RepositoryIntegrityError):
            await repository.atomic_create_entities([
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
        created = await repository.atomic_create_role_managed_entities([
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
        assert await _virtual_entity_id(database, data.id) is None
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
        assert await _virtual_entity_id(database, data.id, _OPEN_SCOPE_TYPE) is None

    async def test_bulk_purge_answers_for_each_named_entity(
        self, database: ExtendedAsyncSAEngine, repository: OpsRepository[_EntityData]
    ) -> None:
        data = await repository.create_entity(_Creator(name="a"))
        absent = _EntityID(uuid.uuid4())

        result = await repository.partial_bulk_purge_entities({
            _EntityID(data.id): _Purger(target=data.id),
            absent: _Purger(target=absent),
        })

        assert set(result.successes) == {data.id}
        assert isinstance(result.errors[absent], EntityNotFoundError)
        assert await _virtual_entity_id(database, data.id) is None
        assert await _row_count(database) == 0


# =============================================================================
# Upsert: the scope stays provisioned idempotently
# =============================================================================


_SIDECAR_FIELD_TYPE = FieldType("test_sidecar")


class _SidecarID(FieldIdentifier):
    @override
    @classmethod
    def field_type(cls) -> FieldType:
        return _SIDECAR_FIELD_TYPE

    """The id of a row that rides beside the graph."""


@dataclass(frozen=True)
class _SidecarData(FieldData):
    """What a sidecar write returns. No entity id: the row joins no graph."""

    id: UUID
    name: str


class _Sidecar(DanglingFieldCreator[EntityLifecycleTestRow, _SidecarData]):
    """A row that rides beside the graph: no node, no owner."""

    def __init__(self, name: str) -> None:
        self.name = name

    @override
    def field_id(self, row: EntityLifecycleTestRow) -> FieldIdentifier:
        return _SidecarID(row.id)

    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def build_row(self) -> EntityLifecycleTestRow:
        return EntityLifecycleTestRow(name=self.name)

    @override
    def to_data(self, row: EntityLifecycleTestRow) -> _SidecarData:
        return _SidecarData(id=row.id, name=row.name)


class TestSidecarCreate:
    async def test_create_provisions_no_scope_and_joins_nothing(
        self, database: ExtendedAsyncSAEngine, repository: OpsRepository[_EntityData]
    ) -> None:
        data = await repository.create_dangling_field(_Sidecar(name="a"))

        assert await _virtual_entity_id(database, data.id) is None
        assert not await _self_membership_exists(database, data.id)

    async def test_atomic_create_writes_every_row(
        self, database: ExtendedAsyncSAEngine, repository: OpsRepository[_EntityData]
    ) -> None:
        items = await repository.atomic_create_dangling_fields([
            _Sidecar(name="a"),
            _Sidecar(name="b"),
        ])

        assert [item.name for item in items] == ["a", "b"]
        assert await _row_count(database) == 2

    async def test_atomic_create_is_all_or_nothing(
        self, database: ExtendedAsyncSAEngine, repository: OpsRepository[_EntityData]
    ) -> None:
        with pytest.raises(RepositoryIntegrityError):
            await repository.atomic_create_dangling_fields([
                _Sidecar(name="a"),
                _Sidecar(name="a"),
            ])

        assert await _row_count(database) == 0


class TestEntityUpsert:
    async def test_upsert_insert_provisions_scope_and_memberships(
        self,
        database: ExtendedAsyncSAEngine,
        repository: OpsRepository[_EntityData],
        parent_id: UUID,
    ) -> None:
        data = await repository.upsert_entity(_Upserter(name="a", parents=(parent_id,)))

        assert await _virtual_entity_id(database, data.id) is not None
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
        with pytest.raises(VirtualEntityNotFound):
            await repository.upsert_entity(_Upserter(name="a", parents=(uuid.uuid4(),)))

        assert await _row_count(database) == 0

    async def test_atomic_upsert_provisions_and_joins_each_entity(
        self,
        database: ExtendedAsyncSAEngine,
        repository: OpsRepository[_EntityData],
        parent_id: UUID,
    ) -> None:
        items = await repository.atomic_upsert_entities([
            _Upserter(name="a", parents=(parent_id,)),
            _Upserter(name="b", parents=(parent_id,)),
        ])

        assert [item.name for item in items] == ["a", "b"]
        for item in items:
            assert await _virtual_entity_id(database, item.id) is not None
            assert await _self_membership_exists(database, item.id)
        assert await _parent_membership_entity_ids(database, parent_id) == {
            item.id for item in items
        }

    async def test_atomic_upsert_updates_an_existing_row_in_place(
        self,
        database: ExtendedAsyncSAEngine,
        repository: OpsRepository[_EntityData],
        parent_id: UUID,
    ) -> None:
        first = await repository.upsert_entity(_Upserter(name="a", parents=(parent_id,)))

        items = await repository.atomic_upsert_entities([
            _Upserter(name="a", note="updated", parents=(parent_id,)),
            _Upserter(name="b", parents=(parent_id,)),
        ])

        assert items[0].id == first.id
        assert items[0].note == "updated"
        assert await _row_count(database) == 2

    async def test_atomic_upsert_is_all_or_nothing(
        self,
        database: ExtendedAsyncSAEngine,
        repository: OpsRepository[_EntityData],
        parent_id: UUID,
    ) -> None:
        with pytest.raises(VirtualEntityNotFound):
            await repository.atomic_upsert_entities([
                _Upserter(name="a", parents=(parent_id,)),
                _Upserter(name="b", parents=(uuid.uuid4(),)),
            ])

        assert await _row_count(database) == 0
