"""Tests for PermissionDBSource.replace_role_permissions."""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator, Sequence
from typing import TYPE_CHECKING

import pytest
import sqlalchemy as sa

from ai.backend.common.data.entity.role import RoleID
from ai.backend.common.data.entity.session import SessionEntityType
from ai.backend.common.data.entity.types import EntityType
from ai.backend.common.data.entity.user import UserEntityType
from ai.backend.manager.data.permission.types import OperationType, Permission
from ai.backend.manager.errors.permission import RoleNotFound

# ORM cluster registration: configure_mappers() (triggered when this isolated
# test registers a domain-cluster row) resolves string relationships against the
# registry. These rows are reachable via relationships but are not otherwise
# imported/registered by this test; _ORM_CLUSTER keeps them live.
from ai.backend.manager.models.agent import AgentRow
from ai.backend.manager.models.image import ImageRow
from ai.backend.manager.models.rbac_models.permission.permission import PermissionRow
from ai.backend.manager.models.rbac_models.role import RoleRow
from ai.backend.manager.models.resource_group import ResourceGroupForDomainRow
from ai.backend.manager.models.specs.permission import PermissionEntry
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

USER_SCOPE_ID = "00000000-0000-4000-8000-00000000fa01"

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
    ResourceGroupForDomainRow,
)


def _entry(
    entity_type: EntityType,
    permission: Permission,
) -> PermissionEntry:
    return PermissionEntry(
        entity_type=EntityType(entity_type),
        permission=permission,
    )


def _owner_entry(entity_type: EntityType) -> PermissionEntry:
    permission = Permission.NONE
    for op in ALL_OWNER_OPS:
        permission |= Permission.from_operation(op)
    return _entry(entity_type, permission)


class TestBulkRolePermissions:
    """Tests for replace_role_permissions on PermissionDBSource."""

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
        seed_permission: PermissionEntry | None = None,
    ) -> uuid.UUID:
        role_id = uuid.uuid4()
        async with db.begin_session() as session:
            session.add(
                RoleRow(
                    scope_type=EntityType("project"),
                    scope_id=uuid.uuid4(),
                    id=role_id,
                    name=role_name,
                )
            )
            await session.flush()
            if seed_permission is not None:
                session.add(
                    PermissionRow(
                        role_id=role_id,
                        entity_type=seed_permission.entity_type,
                        permission=seed_permission.permission,
                    )
                )
            await session.commit()
        return role_id

    async def _seed_permission(
        self,
        db: ExtendedAsyncSAEngine,
        role_id: uuid.UUID,
        entry: PermissionEntry,
    ) -> uuid.UUID:
        permission_id = uuid.uuid4()
        async with db.begin_session() as session:
            session.add(
                PermissionRow(
                    id=permission_id,
                    role_id=role_id,
                    entity_type=entry.entity_type,
                    permission=entry.permission,
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
        stmt = sa.select(PermissionRow.permission).where(
            PermissionRow.role_id == role_id,
            PermissionRow.entity_type == entity_type,
        )
        async with db.begin_readonly_session() as session:
            rows = (await session.execute(stmt)).scalars().all()
        return {permission.to_operation() for permission in rows}

    # ---------- replace_role_permissions ----------

    async def test_replace_swaps_full_permission_set(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        perm_db_source: PermissionDBSource,
    ) -> None:
        role_id = await self._seed_role(db_with_cleanup)
        await self._seed_permission(
            db_with_cleanup,
            role_id,
            _entry(UserEntityType(), Permission.READ),
        )
        new_entry = _owner_entry(SessionEntityType())
        result = await perm_db_source.replace_role_permissions(
            role_id=RoleID(role_id), entries=[new_entry]
        )
        assert len(result) == len(ALL_OWNER_OPS)
        assert await self._count_permissions(db_with_cleanup, role_id) == len(ALL_OWNER_OPS)
        assert await self._list_operations(
            db_with_cleanup, role_id, EntityType(SessionEntityType())
        ) == set(ALL_OWNER_OPS)

    async def test_replace_with_empty_creator_clears_role(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        perm_db_source: PermissionDBSource,
    ) -> None:
        role_id = await self._seed_role(db_with_cleanup)
        await self._seed_permission(
            db_with_cleanup,
            role_id,
            _entry(UserEntityType(), Permission.READ),
        )
        await perm_db_source.replace_role_permissions(role_id=RoleID(role_id), entries=[])
        assert await self._count_permissions(db_with_cleanup, role_id) == 0

    async def test_replace_against_missing_role_raises(
        self, perm_db_source: PermissionDBSource
    ) -> None:
        with pytest.raises(RoleNotFound):
            await perm_db_source.replace_role_permissions(role_id=RoleID(uuid.uuid4()), entries=[])
