"""
Tests for PermissionDBSource bulk role-permission methods:
bulk_add_role_permissions, bulk_remove_role_permissions, replace_role_permissions.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator, Sequence
from typing import TYPE_CHECKING

import pytest
import sqlalchemy as sa

from ai.backend.common.data.permission.types import RBACElementType
from ai.backend.manager.data.permission.types import (
    EntityType,
    OperationType,
    Permission,
    ScopeType,
)
from ai.backend.manager.errors.permission import RoleNotFound

# ORM cluster registration: configure_mappers() (triggered when this isolated
# test registers a domain-cluster row) resolves string relationships against the
# registry. These rows are reachable via relationships but are not otherwise
# imported/registered by this test; _ORM_CLUSTER keeps them live.
from ai.backend.manager.models.agent import AgentRow
from ai.backend.manager.models.image import ImageRow
from ai.backend.manager.models.rbac_models.permission.permission import PermissionRow
from ai.backend.manager.models.rbac_models.role import RoleRow
from ai.backend.manager.models.scaling_group import ScalingGroupForDomainRow
from ai.backend.manager.repositories.base.creator import BulkCreator
from ai.backend.manager.repositories.base.purger import Purger
from ai.backend.manager.repositories.permission_controller.creators import (
    PermissionCreatorSpec,
)
from ai.backend.manager.repositories.permission_controller.db_source.db_source import (
    PermissionDBSource,
)
from ai.backend.testutils.db import TableOrORM, with_tables

if TYPE_CHECKING:
    from ai.backend.manager.models.utils import ExtendedAsyncSAEngine


BULK_PERMISSION_TABLES: Sequence[TableOrORM] = [
    RoleRow,
    PermissionRow,
]

USER_SCOPE_ID = "test-user-uuid"

ALL_OWNER_OPS = (
    OperationType.CREATE,
    OperationType.READ,
    OperationType.UPDATE,
    OperationType.SOFT_DELETE,
    OperationType.HARD_DELETE,
)


_ORM_CLUSTER = (
    AgentRow,
    ImageRow,
    ScalingGroupForDomainRow,
)


def _spec(
    role_id: uuid.UUID,
    entity_type: RBACElementType,
    operation: OperationType,
    scope_type: RBACElementType = RBACElementType.USER,
    scope_id: str = USER_SCOPE_ID,
) -> PermissionCreatorSpec:
    return PermissionCreatorSpec(
        role_id=role_id,
        scope_type=scope_type,
        scope_id=scope_id,
        entity_type=entity_type,
        operation=operation,
    )


def _owner_specs(role_id: uuid.UUID, entity_type: RBACElementType) -> list[PermissionCreatorSpec]:
    return [_spec(role_id, entity_type, op) for op in ALL_OWNER_OPS]


class TestBulkRolePermissions:
    """Tests for bulk add/remove/replace operations on PermissionDBSource."""

    @pytest.fixture
    async def db_with_cleanup(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        async with with_tables(database_connection, BULK_PERMISSION_TABLES):
            yield database_connection

    @pytest.fixture
    def perm_db_source(self, db_with_cleanup: ExtendedAsyncSAEngine) -> PermissionDBSource:
        return PermissionDBSource(db=db_with_cleanup)

    async def _seed_role(
        self,
        db: ExtendedAsyncSAEngine,
        role_name: str = "role_user_test",
        seed_permission: PermissionCreatorSpec | None = None,
    ) -> uuid.UUID:
        role_id = uuid.uuid4()
        async with db.begin_session() as session:
            session.add(RoleRow(id=role_id, name=role_name))
            await session.flush()
            if seed_permission is not None:
                session.add(
                    PermissionRow(
                        role_id=role_id,
                        scope_type=ScopeType(seed_permission.scope_type.value),
                        scope_id=seed_permission.scope_id,
                        entity_type=EntityType(seed_permission.entity_type.value),
                        operation=seed_permission.operation,
                        permission=Permission.from_operation(seed_permission.operation),
                    )
                )
            await session.commit()
        return role_id

    async def _seed_permission(
        self,
        db: ExtendedAsyncSAEngine,
        spec: PermissionCreatorSpec,
    ) -> uuid.UUID:
        permission_id = uuid.uuid4()
        async with db.begin_session() as session:
            session.add(
                PermissionRow(
                    id=permission_id,
                    role_id=spec.role_id,
                    scope_type=ScopeType(spec.scope_type.value),
                    scope_id=spec.scope_id,
                    entity_type=EntityType(spec.entity_type.value),
                    operation=spec.operation,
                    permission=Permission.from_operation(spec.operation),
                )
            )
            await session.commit()
        return permission_id

    async def _count_permissions(
        self,
        db: ExtendedAsyncSAEngine,
        role_id: uuid.UUID,
        entity_type: EntityType | None = None,
    ) -> int:
        stmt = (
            sa.select(sa.func.count())
            .select_from(PermissionRow)
            .where(PermissionRow.role_id == role_id)
        )
        if entity_type is not None:
            stmt = stmt.where(PermissionRow.entity_type == entity_type)
        async with db.begin_readonly_session() as session:
            return (await session.execute(stmt)).scalar_one()

    async def _list_operations(
        self,
        db: ExtendedAsyncSAEngine,
        role_id: uuid.UUID,
        entity_type: EntityType,
    ) -> set[OperationType]:
        stmt = sa.select(PermissionRow.operation).where(
            PermissionRow.role_id == role_id,
            PermissionRow.entity_type == entity_type,
        )
        async with db.begin_readonly_session() as session:
            rows = (await session.execute(stmt)).scalars().all()
        return set(rows)

    # ---------- bulk_add_role_permissions ----------

    async def test_bulk_add_against_missing_role_records_failures(
        self, perm_db_source: PermissionDBSource
    ) -> None:
        ghost_role_id = uuid.uuid4()
        creator = BulkCreator(
            specs=[_spec(ghost_role_id, RBACElementType.SESSION, OperationType.READ)]
        )
        result = await perm_db_source.bulk_add_role_permissions(creator)
        assert result.success_count() == 0
        assert result.has_failures()

    async def test_bulk_add_inserts_given_rows(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        perm_db_source: PermissionDBSource,
    ) -> None:
        role_id = await self._seed_role(db_with_cleanup)
        creator = BulkCreator(specs=_owner_specs(role_id, RBACElementType.SESSION))
        result = await perm_db_source.bulk_add_role_permissions(creator)
        assert result.success_count() == len(ALL_OWNER_OPS)
        assert not result.has_failures()
        assert await self._list_operations(db_with_cleanup, role_id, EntityType.SESSION) == set(
            ALL_OWNER_OPS
        )

    async def test_bulk_add_duplicate_rows_are_recorded_as_failures(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        perm_db_source: PermissionDBSource,
    ) -> None:
        role_id = await self._seed_role(db_with_cleanup)
        creator = BulkCreator(specs=_owner_specs(role_id, RBACElementType.SESSION))
        first = await perm_db_source.bulk_add_role_permissions(creator)
        assert first.success_count() == len(ALL_OWNER_OPS)
        second = await perm_db_source.bulk_add_role_permissions(creator)
        assert second.success_count() == 0
        assert len(second.errors) == len(ALL_OWNER_OPS)
        assert await self._count_permissions(db_with_cleanup, role_id, EntityType.SESSION) == len(
            ALL_OWNER_OPS
        )

    async def test_bulk_add_with_empty_creator_is_noop(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        perm_db_source: PermissionDBSource,
    ) -> None:
        role_id = await self._seed_role(db_with_cleanup)
        before = await self._count_permissions(db_with_cleanup, role_id)
        result = await perm_db_source.bulk_add_role_permissions(BulkCreator(specs=[]))
        after = await self._count_permissions(db_with_cleanup, role_id)
        assert before == after
        assert result.success_count() == 0
        assert not result.has_failures()

    # ---------- bulk_remove_role_permissions ----------

    async def test_bulk_remove_unknown_pk_returns_no_success(
        self, perm_db_source: PermissionDBSource
    ) -> None:
        purgers = [Purger(row_class=PermissionRow, pk_value=uuid.uuid4())]
        result = await perm_db_source.bulk_remove_role_permissions(purgers)
        assert result.success_count() == 0
        assert not result.has_failures()

    async def test_bulk_remove_drops_only_specified_rows(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        perm_db_source: PermissionDBSource,
    ) -> None:
        role_id = await self._seed_role(db_with_cleanup)
        keep_id = await self._seed_permission(
            db_with_cleanup,
            _spec(role_id, RBACElementType.SESSION, OperationType.READ),
        )
        drop_id = await self._seed_permission(
            db_with_cleanup,
            _spec(role_id, RBACElementType.SESSION, OperationType.HARD_DELETE),
        )
        result = await perm_db_source.bulk_remove_role_permissions([
            Purger(row_class=PermissionRow, pk_value=drop_id)
        ])
        assert result.success_count() == 1
        remaining_ids = {keep_id}
        async with db_with_cleanup.begin_readonly_session() as session:
            rows = (
                (
                    await session.execute(
                        sa.select(PermissionRow.id).where(PermissionRow.role_id == role_id)
                    )
                )
                .scalars()
                .all()
            )
        assert set(rows) == remaining_ids

    async def test_bulk_remove_with_empty_list_is_noop(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        perm_db_source: PermissionDBSource,
    ) -> None:
        role_id = await self._seed_role(db_with_cleanup)
        await self._seed_permission(
            db_with_cleanup,
            _spec(role_id, RBACElementType.SESSION, OperationType.READ),
        )
        before = await self._count_permissions(db_with_cleanup, role_id)
        result = await perm_db_source.bulk_remove_role_permissions([])
        after = await self._count_permissions(db_with_cleanup, role_id)
        assert before == after
        assert result.success_count() == 0
        assert not result.has_failures()

    # ---------- replace_role_permissions ----------

    async def test_replace_swaps_full_permission_set(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        perm_db_source: PermissionDBSource,
    ) -> None:
        role_id = await self._seed_role(db_with_cleanup)
        await self._seed_permission(
            db_with_cleanup,
            _spec(role_id, RBACElementType.USER, OperationType.READ),
        )
        new_specs = _owner_specs(role_id, RBACElementType.SESSION)
        result = await perm_db_source.replace_role_permissions(
            role_id=role_id, creator=BulkCreator(specs=new_specs)
        )
        assert result.success_count() == len(new_specs)
        assert await self._count_permissions(db_with_cleanup, role_id) == len(new_specs)
        assert await self._list_operations(db_with_cleanup, role_id, EntityType.SESSION) == set(
            ALL_OWNER_OPS
        )

    async def test_replace_with_empty_creator_clears_role(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        perm_db_source: PermissionDBSource,
    ) -> None:
        role_id = await self._seed_role(db_with_cleanup)
        await self._seed_permission(
            db_with_cleanup,
            _spec(role_id, RBACElementType.USER, OperationType.READ),
        )
        await perm_db_source.replace_role_permissions(
            role_id=role_id, creator=BulkCreator(specs=[])
        )
        assert await self._count_permissions(db_with_cleanup, role_id) == 0

    async def test_replace_against_missing_role_raises(
        self, perm_db_source: PermissionDBSource
    ) -> None:
        with pytest.raises(RoleNotFound):
            await perm_db_source.replace_role_permissions(
                role_id=uuid.uuid4(), creator=BulkCreator(specs=[])
            )
