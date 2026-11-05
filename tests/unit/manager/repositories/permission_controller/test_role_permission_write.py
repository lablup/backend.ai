"""Tests for a role's permission entries written as field rows through the v2 ops."""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator, Sequence
from typing import TYPE_CHECKING

import pytest
import sqlalchemy as sa

from ai.backend.common.data.entity.permission import PermissionID
from ai.backend.common.data.entity.project import ProjectEntityType
from ai.backend.common.data.entity.role import RoleID
from ai.backend.common.data.entity.session import SessionEntityType
from ai.backend.manager.data.permission.permission import PermissionData
from ai.backend.manager.data.permission.status import RoleStatus
from ai.backend.manager.data.permission.types import Permission, RoleSource
from ai.backend.manager.errors.base.field import FieldNotFoundError
from ai.backend.manager.errors.permission import PermissionAlreadyGranted
from ai.backend.manager.errors.role_preset import SystemRoleNotEditable
from ai.backend.manager.models.agent.row import AgentRow
from ai.backend.manager.models.rbac_models.permission.creators import RolePermissionCreator
from ai.backend.manager.models.rbac_models.permission.lookups import RolePermissionOwnerLookup
from ai.backend.manager.models.rbac_models.permission.permission import PermissionRow
from ai.backend.manager.models.rbac_models.permission.purgers import RolePermissionPurger
from ai.backend.manager.models.rbac_models.permission.updaters import RolePermissionUpdater
from ai.backend.manager.models.rbac_models.role.row import RoleRow
from ai.backend.manager.models.resource_group.row import ResourceGroupForDomainRow
from ai.backend.manager.repositories.ops.repository import OpsRepository
from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider
from ai.backend.manager.repositories.permission_controller.db_source.db_source import (
    PermissionDBSource,
)
from ai.backend.manager.types import OptionalState
from ai.backend.testutils.db import TableOrORM, with_tables

if TYPE_CHECKING:
    from ai.backend.manager.models.utils import ExtendedAsyncSAEngine


TABLES: Sequence[TableOrORM] = [RoleRow, PermissionRow]

_ORM_CLUSTER = (AgentRow, ResourceGroupForDomainRow)


class TestRolePermissionWrite:
    @pytest.fixture
    async def db_with_tables(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        async with with_tables(database_connection, TABLES):
            yield database_connection

    @pytest.fixture
    def repository(self, db_with_tables: ExtendedAsyncSAEngine) -> OpsRepository[PermissionData]:
        return OpsRepository(V2DBOpsProvider(db_with_tables))

    @pytest.fixture
    async def role_id(self, db_with_tables: ExtendedAsyncSAEngine) -> RoleID:
        role_id = RoleID(uuid.uuid4())
        async with db_with_tables.begin_session() as db_sess:
            await db_sess.execute(
                sa.insert(RoleRow).values(
                    scope_type=ProjectEntityType(),
                    scope_id=uuid.uuid4(),
                    id=role_id,
                    name="reader",
                    source=RoleSource.CUSTOM,
                    status=RoleStatus.ACTIVE,
                )
            )
        return role_id

    def _read_sessions(self) -> RolePermissionCreator:
        return RolePermissionCreator(entity_type=SessionEntityType(), permission=Permission.READ)

    async def test_create_and_purge_are_answered_by_the_role(
        self,
        repository: OpsRepository[PermissionData],
        db_with_tables: ExtendedAsyncSAEngine,
        role_id: RoleID,
    ) -> None:
        created = await repository.create_field(role_id, self._read_sessions())

        assert created.role_id == role_id
        assert created.permission == Permission.READ
        owners = await repository.field_owners(RolePermissionOwnerLookup(), [created.id])
        assert owners == {created.id: role_id}

        result = await repository.partial_bulk_purge_field_entities({
            created.id: RolePermissionPurger(permission_id=created.id)
        })
        assert set(result.successes) == {created.id}
        async with db_with_tables.begin_readonly_session() as db_sess:
            assert await db_sess.scalar(sa.select(sa.func.count()).select_from(PermissionRow)) == 0

    async def test_duplicate_entry_is_refused(
        self, repository: OpsRepository[PermissionData], role_id: RoleID
    ) -> None:
        await repository.create_field(role_id, self._read_sessions())

        with pytest.raises(PermissionAlreadyGranted):
            await repository.create_field(role_id, self._read_sessions())

    async def test_partial_purge_answers_for_each_entry(
        self, repository: OpsRepository[PermissionData], role_id: RoleID
    ) -> None:
        created = await repository.create_field(role_id, self._read_sessions())
        unknown = PermissionID(uuid.uuid4())

        result = await repository.partial_bulk_purge_field_entities({
            created.id: RolePermissionPurger(permission_id=created.id),
            unknown: RolePermissionPurger(permission_id=unknown),
        })

        assert set(result.successes) == {created.id}
        assert isinstance(result.errors[unknown], FieldNotFoundError)


class TestSystemRolePermissionWrite:
    """A SYSTEM role's entries follow its role preset: no write reaches them directly."""

    @pytest.fixture
    async def db_with_tables(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        async with with_tables(database_connection, TABLES):
            yield database_connection

    @pytest.fixture
    def repository(self, db_with_tables: ExtendedAsyncSAEngine) -> OpsRepository[PermissionData]:
        return OpsRepository(V2DBOpsProvider(db_with_tables))

    @pytest.fixture
    async def system_role_id(self, db_with_tables: ExtendedAsyncSAEngine) -> RoleID:
        role_id = RoleID(uuid.uuid4())
        async with db_with_tables.begin_session() as db_sess:
            await db_sess.execute(
                sa.insert(RoleRow).values(
                    scope_type=ProjectEntityType(),
                    scope_id=uuid.uuid4(),
                    id=role_id,
                    name="project-admin",
                    source=RoleSource.SYSTEM,
                    status=RoleStatus.ACTIVE,
                )
            )
        return role_id

    @pytest.fixture
    async def system_entry_id(
        self, db_with_tables: ExtendedAsyncSAEngine, system_role_id: RoleID
    ) -> PermissionID:
        """An entry the role preset wrote, inserted the way the preset write does."""
        entry_id = PermissionID(uuid.uuid4())
        async with db_with_tables.begin_session() as db_sess:
            await db_sess.execute(
                sa.insert(PermissionRow).values(
                    id=entry_id,
                    role_id=system_role_id,
                    entity_type=SessionEntityType(),
                    permission=Permission.READ,
                )
            )
        return entry_id

    async def _entry_count(self, db: ExtendedAsyncSAEngine) -> int:
        async with db.begin_readonly_session() as db_sess:
            count = await db_sess.scalar(sa.select(sa.func.count()).select_from(PermissionRow))
        return int(count or 0)

    async def test_an_entry_of_a_system_role_is_not_updated(
        self,
        repository: OpsRepository[PermissionData],
        db_with_tables: ExtendedAsyncSAEngine,
        system_entry_id: PermissionID,
    ) -> None:
        with pytest.raises(SystemRoleNotEditable):
            await repository.update(
                RolePermissionUpdater(
                    permission_id=system_entry_id,
                    permission=OptionalState.update(Permission.UPDATE),
                )
            )
        async with db_with_tables.begin_readonly_session() as db_sess:
            stored = await db_sess.scalar(
                sa.select(PermissionRow.permission).where(PermissionRow.id == system_entry_id)
            )
        assert stored == Permission.READ

    async def test_an_entry_of_a_system_role_is_not_purged(
        self,
        repository: OpsRepository[PermissionData],
        db_with_tables: ExtendedAsyncSAEngine,
        system_entry_id: PermissionID,
    ) -> None:
        result = await repository.partial_bulk_purge_field_entities({
            system_entry_id: RolePermissionPurger(permission_id=system_entry_id)
        })
        assert isinstance(result.errors[system_entry_id], SystemRoleNotEditable)
        assert await self._entry_count(db_with_tables) == 1

    async def test_the_entries_of_a_system_role_are_not_replaced(
        self,
        db_with_tables: ExtendedAsyncSAEngine,
        system_role_id: RoleID,
        system_entry_id: PermissionID,
    ) -> None:
        with pytest.raises(SystemRoleNotEditable):
            await PermissionDBSource(db_with_tables).replace_role_permissions(system_role_id, [])
        assert await self._entry_count(db_with_tables) == 1
