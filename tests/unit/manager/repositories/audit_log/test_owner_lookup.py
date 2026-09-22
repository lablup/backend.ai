"""The entity each audit record is answered for, read against a real ``audit_logs`` table."""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator

import pytest

from ai.backend.common.data.entity.audit_log import AuditLogID
from ai.backend.common.data.entity.session import SessionEntityType
from ai.backend.common.data.entity.types import GlobalEntityType, RuntimeEntityID
from ai.backend.manager.actions.types import ActionKind, OperationStatus
from ai.backend.manager.data.audit_log.types import AuditLogData
from ai.backend.manager.models.audit_log.lookups import AuditLogOwnerLookup
from ai.backend.manager.models.audit_log.row import AuditLogRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.ops.repository import OpsRepository
from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider
from ai.backend.testutils.db import with_tables

_GLOBAL_OWNER = RuntimeEntityID(GlobalEntityType(), uuid.UUID(int=0))


class TestAuditLogOwnerLookup:
    @pytest.fixture
    async def db_with_cleanup(
        self, database_connection: ExtendedAsyncSAEngine
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        async with with_tables(database_connection, [AuditLogRow]):
            yield database_connection

    @pytest.fixture
    def repository(self, db_with_cleanup: ExtendedAsyncSAEngine) -> OpsRepository[AuditLogData]:
        return OpsRepository[AuditLogData](V2DBOpsProvider(db_with_cleanup))

    async def _insert_row(
        self,
        db: ExtendedAsyncSAEngine,
        *,
        action_kind: ActionKind,
        entity_type: str | None,
        entity_id: str | None,
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
                )
            )
        return row_id

    async def test_a_record_about_an_entity_is_answered_for_by_that_entity(
        self, db_with_cleanup: ExtendedAsyncSAEngine, repository: OpsRepository[AuditLogData]
    ) -> None:
        session_id = uuid.uuid4()
        row_id = await self._insert_row(
            db_with_cleanup,
            action_kind=ActionKind.SINGLE_ENTITY,
            entity_type=SessionEntityType.name(),
            entity_id=str(session_id),
        )

        owners = await repository.runtime_field_owners(AuditLogOwnerLookup(), [row_id])

        assert owners == {row_id: RuntimeEntityID(SessionEntityType(), session_id)}

    @pytest.mark.parametrize(
        ("action_kind", "entity_type", "entity_id"),
        [
            (ActionKind.RELATION, None, None),
            (ActionKind.GLOBAL, GlobalEntityType.name(), None),
            (ActionKind.LOOKUP, SessionEntityType.name(), None),
            (ActionKind.SINGLE_ENTITY, "keypair", "AKIAIOSFODNN7EXAMPLE"),
        ],
    )
    async def test_a_record_naming_no_entity_by_uuid_is_answered_for_by_global(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        repository: OpsRepository[AuditLogData],
        action_kind: ActionKind,
        entity_type: str | None,
        entity_id: str | None,
    ) -> None:
        row_id = await self._insert_row(
            db_with_cleanup, action_kind=action_kind, entity_type=entity_type, entity_id=entity_id
        )

        owners = await repository.runtime_field_owners(AuditLogOwnerLookup(), [row_id])

        assert owners == {row_id: _GLOBAL_OWNER}

    async def test_an_absent_record_has_no_owner(
        self, db_with_cleanup: ExtendedAsyncSAEngine, repository: OpsRepository[AuditLogData]
    ) -> None:
        owners = await repository.runtime_field_owners(
            AuditLogOwnerLookup(), [AuditLogID(uuid.uuid4())]
        )

        assert owners == {}
