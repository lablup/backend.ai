import asyncio
import logging
import uuid
from typing import Final, override

import sqlalchemy as sa

from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.models.audit_log import AuditLogRow, OperationStatus
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.reporters.types import (
    AbstractReporter,
    FinishedActionMessage,
    StartedActionMessage,
)

NULL_UUID: Final[uuid.UUID] = uuid.UUID("00000000-0000-0000-0000-000000000000")
UNKNOWN_ENTITY_ID: Final[str] = "(unknown)"


log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class AuditLogReporter(AbstractReporter):
    _db: ExtendedAsyncSAEngine

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db = db

    async def _generate_log(self, action_message: StartedActionMessage) -> None:
        async with self._db.begin_session() as db_sess:
            db_row = AuditLogRow(
                action_id=action_message.action_id,
                entity_type=action_message.entity_type,
                operation=action_message.operation_type,
                created_at=action_message.created_at,
                entity_id=action_message.entity_id or UNKNOWN_ENTITY_ID,
                # TODO: Inject request_id.
                request_id=NULL_UUID,
                description="Task is running...",
                status=OperationStatus.RUNNING,
            )

            db_sess.add(db_row)
            await db_sess.flush()

    async def _update_log(self, action_message: FinishedActionMessage) -> None:
        async with self._db.begin_session() as db_sess:
            query = sa.select(AuditLogRow).where(AuditLogRow.action_id == action_message.action_id)
            db_row: AuditLogRow = await db_sess.scalar(query)
            if not db_row:
                log.error(f'AuditLog with action_id "{action_message.action_id}" not found in DB')
                return

            db_row.status = action_message.status
            db_row.description = action_message.description
            db_row.duration = action_message.duration
            if action_message.entity_id:
                db_row.entity_id = action_message.entity_id
            await db_sess.flush()

    @override
    async def report_started(self, message: StartedActionMessage) -> None:
        asyncio.create_task(self._generate_log(message))

    @override
    async def report_finished(self, message: FinishedActionMessage) -> None:
        asyncio.create_task(self._update_log(message))
