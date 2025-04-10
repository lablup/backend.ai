import asyncio
import logging
import uuid
from contextvars import ContextVar
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Final, Optional

from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.actions.action import BaseAction, ProcessResult
from ai.backend.manager.actions.monitors.monitor import ActionMonitor
from ai.backend.manager.models.audit_log import AuditLogRow, OperationStatus
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.types import Sentinel

NULL_UUID: Final[uuid.UUID] = uuid.UUID("00000000-0000-0000-0000-000000000000")
UNKNOWN_ENTITY_ID: Final[str] = "(unknown)"


log = BraceStyleAdapter(logging.getLogger(__spec__.name))


@dataclass
class AuditLogInfo:
    # TODO: Add live configs here
    pass


@dataclass
class AuditLogMeta:
    info: AuditLogInfo
    log_id: uuid.UUID


@dataclass
class AuditLog:
    action: BaseAction
    meta: AuditLogMeta
    result: ProcessResult


class AuditLogger:
    _queue: asyncio.Queue[AuditLog | Sentinel]
    _stopped: bool
    _db: ExtendedAsyncSAEngine

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db = db
        self._queue = asyncio.Queue()
        self._stopped = True
        self._log_task: Optional[asyncio.Task] = None

    async def log_queue(self) -> None:
        while not self._stopped:
            audit_log = await self._queue.get()
            if audit_log == Sentinel.token:
                return

            async with self._db.begin_session() as db_sess:
                action = audit_log.action
                result = audit_log.result

                if result.result:
                    entity_id = result.result.entity_id()
                    if not entity_id:
                        log.error(
                            f'Following ActionType doesn\'t provide entity type!: "{type(action)}"'
                        )
                        entity_id = UNKNOWN_ENTITY_ID
                else:
                    entity_id = UNKNOWN_ENTITY_ID

                db_row: AuditLogRow = await db_sess.get(AuditLogRow, audit_log.meta.log_id)
                if not db_row:
                    log.error(f'Auditlog with id "{audit_log.meta.log_id}" not found in DB')

                db_row.status = OperationStatus(result.meta.status)
                db_row.description = result.meta.description
                db_row.duration = timedelta(seconds=result.meta.duration)
                db_row.entity_id = entity_id
                await db_sess.flush()

    async def init(self, action: BaseAction, info: AuditLogInfo) -> Optional[AuditLogMeta]:
        if self._stopped:
            return None

        async with self._db.begin_session() as db_sess:
            db_row = AuditLogRow(
                entity_type=action.entity_type(),
                operation=action.operation_type(),
                entity_id=action.entity_id() or UNKNOWN_ENTITY_ID,
                request_id=NULL_UUID,
                description="Task is running...",
                duration=timedelta(0),
                status=OperationStatus.RUNNING,
                created_at=datetime.now(),
            )

            db_sess.add(db_row)
            await db_sess.flush()

        return AuditLogMeta(info=info, log_id=db_row.id)

    async def log(self, audit_log: AuditLog) -> None:
        await self._queue.put(audit_log)

    def start(self) -> None:
        self._stopped = False
        if not self._log_task:
            self._log_task = asyncio.create_task(self.log_queue())

    async def stop(self) -> None:
        self._stopped = True

        if self._log_task:
            try:
                await self._queue.put(Sentinel.token)
                await self._log_task
            except asyncio.CancelledError:
                pass
            self._log_task = None


class AuditLogManager(ActionMonitor):
    _log_context: ContextVar[AuditLogMeta] = ContextVar("log_context")
    _audit_logger: AuditLogger

    def __init__(self, audit_logger: AuditLogger) -> None:
        self._audit_logger = audit_logger

    async def prepare(self, action: BaseAction) -> None:
        # TODO: Inject live configs into AuditLogInfo
        if audit_log_meta := await self._audit_logger.init(action, AuditLogInfo()):
            self._log_context.set(audit_log_meta)

    async def done(self, action: BaseAction, result: ProcessResult) -> None:
        if audit_log_meta := self._log_context.get(None):
            audit_log = AuditLog(action=action, result=result, meta=audit_log_meta)
            await self._audit_logger.log(audit_log)

    def start(self) -> None:
        self._audit_logger.start()

    async def stop(self) -> None:
        await self._audit_logger.stop()
