"""The owner candidates of each audit record, read against real ``audit_logs`` tables."""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator

import pytest

from ai.backend.common.data.entity.audit_log import AuditLogID
from ai.backend.common.data.entity.project import ProjectEntityType
from ai.backend.common.data.entity.session import SessionEntityType
from ai.backend.common.data.entity.types import EntityType, RuntimeEntityID
from ai.backend.common.data.entity.user import UserEntityType
from ai.backend.manager.actions.types import ActionKind, OperationStatus
from ai.backend.manager.data.audit_log.types import AuditLogData
from ai.backend.manager.models.audit_log.owner_candidates import AuditLogOwnerCandidates
from ai.backend.manager.models.audit_log.row import AuditLogRow
from ai.backend.manager.models.audit_log.scope_row import AuditLogScopeRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.ops.repository import OpsRepository
from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider
from ai.backend.testutils.db import with_tables


class TestAuditLogOwnerCandidates:
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
        action_kind: ActionKind,
        entity_type: EntityType | None = None,
        entity_id: uuid.UUID | None = None,
        triggered_by: str | None = None,
        scopes: list[tuple[EntityType, uuid.UUID]] | None = None,
    ) -> AuditLogID:
        row_id = AuditLogID(uuid.uuid4())
        async with db.begin_session() as db_sess:
            db_sess.add(
                AuditLogRow(
                    id=row_id,
                    action_kind=action_kind,
                    entity_type=entity_type,
                    entity_id=entity_id,
                    operation="get",
                    action_name="test",
                    action_id=uuid.uuid4(),
                    description="test",
                    status=OperationStatus.SUCCESS,
                    triggered_by=triggered_by,
                )
            )
            await db_sess.flush()
            db_sess.add_all([
                AuditLogScopeRow(audit_log_id=row_id, scope_type=scope_type, scope_id=scope_id)
                for scope_type, scope_id in scopes or []
            ])
        return row_id

    async def test_a_record_names_its_entity_its_scopes_and_its_trigger(
        self, db_with_cleanup: ExtendedAsyncSAEngine, repository: OpsRepository[AuditLogData]
    ) -> None:
        session_id, project_id, user_id = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
        row_id = await self._insert_row(
            db_with_cleanup,
            action_kind=ActionKind.SCOPE,
            entity_type=SessionEntityType(),
            entity_id=session_id,
            triggered_by=str(user_id),
            scopes=[(ProjectEntityType(), project_id)],
        )

        candidates = await repository.field_owner_candidates(AuditLogOwnerCandidates(), [row_id])

        assert set(candidates[row_id]) == {
            RuntimeEntityID(SessionEntityType(), session_id),
            RuntimeEntityID(ProjectEntityType(), project_id),
            RuntimeEntityID(UserEntityType(), user_id),
        }

    async def test_a_relation_record_names_each_scope(
        self, db_with_cleanup: ExtendedAsyncSAEngine, repository: OpsRepository[AuditLogData]
    ) -> None:
        project_id, user_id = uuid.uuid4(), uuid.uuid4()
        row_id = await self._insert_row(
            db_with_cleanup,
            action_kind=ActionKind.RELATION,
            scopes=[
                (ProjectEntityType(), project_id),
                (UserEntityType(), user_id),
            ],
        )

        candidates = await repository.field_owner_candidates(AuditLogOwnerCandidates(), [row_id])

        assert set(candidates[row_id]) == {
            RuntimeEntityID(ProjectEntityType(), project_id),
            RuntimeEntityID(UserEntityType(), user_id),
        }

    async def test_a_record_naming_no_entity_and_no_user_has_no_candidate(
        self, db_with_cleanup: ExtendedAsyncSAEngine, repository: OpsRepository[AuditLogData]
    ) -> None:
        row_id = await self._insert_row(
            db_with_cleanup, action_kind=ActionKind.GLOBAL, triggered_by="system"
        )

        candidates = await repository.field_owner_candidates(AuditLogOwnerCandidates(), [row_id])

        assert candidates == {}

    async def test_an_absent_record_has_no_candidate(
        self, db_with_cleanup: ExtendedAsyncSAEngine, repository: OpsRepository[AuditLogData]
    ) -> None:
        candidates = await repository.field_owner_candidates(
            AuditLogOwnerCandidates(), [AuditLogID(uuid.uuid4())]
        )

        assert candidates == {}
