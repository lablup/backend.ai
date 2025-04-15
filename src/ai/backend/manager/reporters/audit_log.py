import logging
from typing import override

from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.models.audit_log import AuditLogRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.reporters.base import (
    AbstractReporter,
    FinishedActionMessage,
    StartedActionMessage,
)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class AuditLogReporter(AbstractReporter):
    _db: ExtendedAsyncSAEngine

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db = db

    async def _generate_log(self, action_message: FinishedActionMessage) -> None:
        async with self._db.begin_session() as db_sess:
            db_row = AuditLogRow(
                action_id=action_message.action_id,
                entity_type=action_message.entity_type,
                operation=action_message.operation_type,
                created_at=action_message.created_at,
                entity_id=action_message.entity_id,
                request_id=action_message.request_id,
                description=action_message.description,
                status=action_message.status,
                duration=action_message.duration,
            )

            db_sess.add(db_row)
            await db_sess.flush()

    @override
    async def report_started(self, message: StartedActionMessage) -> None:
        pass

    @override
    async def report_finished(self, message: FinishedActionMessage) -> None:
        await self._generate_log(message)
