"""The rows each audit-log scope selects, read against real ``audit_logs`` tables."""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator

import pytest

from ai.backend.common.data.entity.audit_log import AuditLogID
from ai.backend.common.data.entity.project import ProjectEntityType
from ai.backend.common.data.entity.session import SessionEntityType
from ai.backend.common.data.entity.types import EntityType, RuntimeEntityID
from ai.backend.manager.actions.types import ActionKind, OperationStatus
from ai.backend.manager.data.audit_log.types import AuditLogData
from ai.backend.manager.models.audit_log.row import AuditLogRow
from ai.backend.manager.models.audit_log.scope_row import AuditLogScopeRow
from ai.backend.manager.models.audit_log.scopes import EntityAuditLogTarget
from ai.backend.manager.models.audit_log.searchers import AuditLogSearcher
from ai.backend.manager.models.specs.pagination import OffsetPagination
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.ops.repository import OpsRepository
from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider
from ai.backend.testutils.db import with_tables


class TestEntityAuditLogTarget:
    @pytest.fixture
    async def db_with_cleanup(
        self, database_connection: ExtendedAsyncSAEngine
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        async with with_tables(database_connection, [AuditLogRow, AuditLogScopeRow]):
            yield database_connection

    @pytest.fixture
    def repository(self, db_with_cleanup: ExtendedAsyncSAEngine) -> OpsRepository[AuditLogData]:
        return OpsRepository[AuditLogData](V2DBOpsProvider(db_with_cleanup))

    async def _insert_row(
        self,
        db: ExtendedAsyncSAEngine,
        *,
        entity_type: EntityType,
        entity_id: uuid.UUID,
        scopes: list[tuple[EntityType, uuid.UUID]] | None = None,
    ) -> AuditLogID:
        row_id = AuditLogID(uuid.uuid4())
        async with db.begin_session() as db_sess:
            db_sess.add(
                AuditLogRow(
                    id=row_id,
                    action_kind=ActionKind.SCOPE,
                    entity_type=entity_type,
                    entity_id=entity_id,
                    operation="get",
                    action_name="test",
                    action_id=uuid.uuid4(),
                    description="test",
                    status=OperationStatus.SUCCESS,
                )
            )
            await db_sess.flush()
            db_sess.add_all([
                AuditLogScopeRow(audit_log_id=row_id, scope_type=scope_type, scope_id=scope_id)
                for scope_type, scope_id in scopes or []
            ])
        return row_id

    async def test_selects_the_runs_that_touched_it_and_the_runs_in_it(
        self, db_with_cleanup: ExtendedAsyncSAEngine, repository: OpsRepository[AuditLogData]
    ) -> None:
        project_id = uuid.uuid4()
        touched = await self._insert_row(
            db_with_cleanup, entity_type=ProjectEntityType(), entity_id=project_id
        )
        within = await self._insert_row(
            db_with_cleanup,
            entity_type=SessionEntityType(),
            entity_id=uuid.uuid4(),
            scopes=[(ProjectEntityType(), project_id)],
        )
        await self._insert_row(
            db_with_cleanup,
            entity_type=SessionEntityType(),
            entity_id=uuid.uuid4(),
            scopes=[(ProjectEntityType(), uuid.uuid4())],
        )

        result = await repository.search_in_scopes(
            [EntityAuditLogTarget(owner=RuntimeEntityID(ProjectEntityType(), project_id))],
            AuditLogSearcher(pagination=OffsetPagination(limit=10, offset=0)),
        )

        assert {item.id for item in result.items} == {touched, within}
