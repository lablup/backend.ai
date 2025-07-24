import logging
from typing import Final, override

from ai.backend.common.contexts.request_id import current_request_id
from ai.backend.common.contexts.user import current_user
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.actions.action import BaseAction, BaseActionTriggerMeta, ProcessResult
from ai.backend.manager.actions.monitors.monitor import ActionMonitor
from ai.backend.manager.models.audit_log import AuditLogRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine

_BLANK_ID: Final[str] = "(unknown)"


log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class AuditLogMonitor(ActionMonitor):
    _db: ExtendedAsyncSAEngine

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db = db

    async def _generate_log(self, action: BaseAction, result: ProcessResult) -> None:
        async with self._db.begin_session() as db_sess:
            user = current_user()
            db_row = AuditLogRow(
                action_id=result.meta.action_id,
                entity_type=action.entity_type(),
                operation=action.operation_type(),
                created_at=result.meta.started_at,
                entity_id=result.meta.entity_id or _BLANK_ID,
                request_id=current_request_id() or _BLANK_ID,
                triggered_by=str(user.user_id) if user else None,
                description=result.meta.description,
                status=result.meta.status,
                duration=result.meta.duration,
            )

            db_sess.add(db_row)
            await db_sess.flush()

    @override
    async def prepare(self, action: BaseAction, meta: BaseActionTriggerMeta) -> None:
        pass

    @override
    async def done(self, action: BaseAction, result: ProcessResult) -> None:
        await self._generate_log(action, result)
