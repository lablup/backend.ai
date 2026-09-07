"""Tests for role update, soft delete and purge through the v2 ops."""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator, Sequence
from typing import TYPE_CHECKING

import pytest
import sqlalchemy as sa

from ai.backend.common.data.entity.role import RoleID
from ai.backend.common.data.permission.types import RoleSource
from ai.backend.manager.data.permission.role import RoleData
from ai.backend.manager.data.permission.status import RoleStatus
from ai.backend.manager.errors.repository import EntityNotFoundError, EntityWriteRefusedError
from ai.backend.manager.errors.role_preset import SystemRoleNotEditable
from ai.backend.manager.models.agent import AgentRow
from ai.backend.manager.models.entity_label.row import EntityLabelRow
from ai.backend.manager.models.rbac_models.association_scopes_entities import (
    AssociationScopesEntitiesRow,
)
from ai.backend.manager.models.rbac_models.permission.permission import PermissionRow
from ai.backend.manager.models.rbac_models.role import RoleRow
from ai.backend.manager.models.rbac_models.role.purgers import RolePurger
from ai.backend.manager.models.rbac_models.role.updaters import RoleSoftDeleteUpdater, RoleUpdater
from ai.backend.manager.models.resource_group import ResourceGroupForDomainRow
from ai.backend.manager.models.virtual_entity.virtual_entity import VirtualEntityRow
from ai.backend.manager.repositories.ops.repository import OpsRepository
from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider
from ai.backend.manager.types import OptionalState
from ai.backend.testutils.db import TableOrORM, with_tables

if TYPE_CHECKING:
    from ai.backend.manager.models.utils import ExtendedAsyncSAEngine


TABLES: Sequence[TableOrORM] = [
    RoleRow,
    AssociationScopesEntitiesRow,
    PermissionRow,
    VirtualEntityRow,
    EntityLabelRow,
]

_ORM_CLUSTER = (AgentRow, ResourceGroupForDomainRow)


class TestRoleWrite:
    @pytest.fixture
    async def db_with_tables(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        async with with_tables(database_connection, TABLES):
            yield database_connection

    @pytest.fixture
    def repository(self, db_with_tables: ExtendedAsyncSAEngine) -> OpsRepository[RoleData]:
        return OpsRepository(V2DBOpsProvider(db_with_tables))

    async def _insert_role(self, db: ExtendedAsyncSAEngine, source: RoleSource) -> RoleID:
        role_id = RoleID(uuid.uuid4())
        async with db.begin_session() as db_sess:
            await db_sess.execute(
                sa.insert(RoleRow).values(
                    id=role_id,
                    name=f"role-{source.value}",
                    source=source,
                    status=RoleStatus.ACTIVE,
                )
            )
        return role_id

    async def _source_of(self, db: ExtendedAsyncSAEngine, role_id: RoleID) -> RoleSource | None:
        async with db.begin_session() as db_sess:
            source = await db_sess.scalar(sa.select(RoleRow.source).where(RoleRow.id == role_id))
        return None if source is None else RoleSource(source)

    def _rename(self, role_id: RoleID) -> RoleUpdater:
        return RoleUpdater(role_id=role_id, name=OptionalState.update("renamed"))

    async def test_custom_role_update_delete_purge_pass(
        self, repository: OpsRepository[RoleData], db_with_tables: ExtendedAsyncSAEngine
    ) -> None:
        role_id = await self._insert_role(db_with_tables, RoleSource.CUSTOM)
        updated = await repository.update_guarded(self._rename(role_id))
        assert updated.name == "renamed"
        deleted = await repository.update_guarded(RoleSoftDeleteUpdater(role_id=role_id))
        assert deleted.status == RoleStatus.DELETED
        assert deleted.deleted_at is not None
        purged = await repository.purge_entity(RolePurger(role_id=role_id))
        assert purged.id == role_id
        assert await self._source_of(db_with_tables, role_id) is None

    async def test_system_role_update_is_refused(
        self, repository: OpsRepository[RoleData], db_with_tables: ExtendedAsyncSAEngine
    ) -> None:
        role_id = await self._insert_role(db_with_tables, RoleSource.SYSTEM)
        with pytest.raises(EntityWriteRefusedError):
            await repository.update_guarded(self._rename(role_id))

    async def test_system_role_delete_is_refused(
        self, repository: OpsRepository[RoleData], db_with_tables: ExtendedAsyncSAEngine
    ) -> None:
        role_id = await self._insert_role(db_with_tables, RoleSource.SYSTEM)
        with pytest.raises(EntityWriteRefusedError):
            await repository.update_guarded(RoleSoftDeleteUpdater(role_id=role_id))

    async def test_system_role_purge_is_refused(
        self, repository: OpsRepository[RoleData], db_with_tables: ExtendedAsyncSAEngine
    ) -> None:
        role_id = await self._insert_role(db_with_tables, RoleSource.SYSTEM)
        with pytest.raises(SystemRoleNotEditable):
            await repository.purge_entity(RolePurger(role_id=role_id))
        assert await self._source_of(db_with_tables, role_id) == RoleSource.SYSTEM

    async def test_missing_role_raises_not_found(self, repository: OpsRepository[RoleData]) -> None:
        role_id = RoleID(uuid.uuid4())
        with pytest.raises(EntityNotFoundError):
            await repository.update_guarded(self._rename(role_id))
        with pytest.raises(EntityNotFoundError):
            await repository.update_guarded(RoleSoftDeleteUpdater(role_id=role_id))
        with pytest.raises(EntityNotFoundError):
            await repository.purge_entity(RolePurger(role_id=role_id))
