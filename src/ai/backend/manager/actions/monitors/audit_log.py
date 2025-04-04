import asyncio
import logging
import uuid
from datetime import timedelta
from typing import Final, override

from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.actions.action import BaseAction, ProcessResult
from ai.backend.manager.actions.monitors.monitor import ActionMonitor
from ai.backend.manager.models.audit_log import AuditLogEntityType, AuditLogRow, OperationStatus
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


NULL_UUID: Final[uuid.UUID] = uuid.UUID("00000000-0000-0000-0000-000000000000")


class AuditLogReporter(ActionMonitor):
    _db: ExtendedAsyncSAEngine

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db = db

    @override
    async def prepare(self, action: BaseAction) -> None:
        pass

    @override
    async def done(self, action: BaseAction, result: ProcessResult) -> None:
        async def _report() -> None:
            if result.result:
                entity_id = result.result.entity_id()
                if not entity_id:
                    log.error(
                        f'Following ActionType doesn\'t provide entity type!: "{type(action)}"'
                    )
                    entity_id = NULL_UUID
            else:
                entity_id = NULL_UUID

            async with self._db.begin_session() as db_session:
                db_session.add(
                    AuditLogRow(
                        entity_type=AuditLogEntityType(action.entity_type()),
                        operation=action.operation_type(),
                        entity_id=entity_id,
                        request_id=NULL_UUID,
                        description=result.meta.description,
                        duration=timedelta(seconds=result.meta.duration),
                        created_at=result.meta.started_at,
                        status=OperationStatus(result.meta.status),
                    )
                )
                await db_session.flush()

        asyncio.create_task(_report())
