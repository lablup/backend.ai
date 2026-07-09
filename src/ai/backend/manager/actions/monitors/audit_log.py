from __future__ import annotations

import logging
import uuid
from typing import override

from ai.backend.common.contexts.request_id import current_request_id
from ai.backend.common.contexts.user import current_user, triggered_user
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.actions.action import BaseAction, BaseActionTriggerMeta, ProcessResult
from ai.backend.manager.actions.monitors.monitor import ActionMonitor
from ai.backend.manager.actions.types import BLANK_ID
from ai.backend.manager.data.audit_log.types import AuditLogData
from ai.backend.manager.repositories.audit_log import AuditLogCreatorSpec, AuditLogRepository
from ai.backend.manager.repositories.base import Creator

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class AuditLogMonitor(ActionMonitor):
    _repository: AuditLogRepository

    def __init__(self, repository: AuditLogRepository) -> None:
        self._repository = repository

    async def _generate_log(self, action: BaseAction, result: ProcessResult) -> None:
        # triggered_by = the caller who triggered the request; acted_as = the effective
        # (acting) subject. They differ only while a super admin is impersonating.
        trigger = triggered_user()
        acting = current_user()
        data = AuditLogData(
            id=uuid.uuid4(),
            action_id=result.meta.action_id,
            entity_type=action.entity_type(),
            operation=action.operation_type(),
            created_at=result.meta.started_at,
            description=result.meta.description,
            status=result.meta.status,
            entity_id=result.meta.entity_id or BLANK_ID,
            request_id=current_request_id() or BLANK_ID,
            triggered_by=str(trigger.user_id) if trigger else None,
            acted_as=str(acting.user_id) if acting else None,
            duration=result.meta.duration,
        )
        creator = Creator(
            spec=AuditLogCreatorSpec(
                action_id=data.action_id,
                entity_type=data.entity_type,
                operation=data.operation,
                created_at=data.created_at,
                description=data.description,
                status=data.status,
                entity_id=data.entity_id,
                request_id=data.request_id,
                triggered_by=data.triggered_by,
                acted_as=data.acted_as,
                duration=data.duration,
            )
        )
        await self._repository.create(creator)

    @override
    async def prepare(self, action: BaseAction, meta: BaseActionTriggerMeta) -> None:
        pass

    @override
    async def done(self, action: BaseAction, result: ProcessResult) -> None:
        await self._generate_log(action, result)
