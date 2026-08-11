from __future__ import annotations

import logging
from typing import override

from ai.backend.common.contexts.request_id import current_request_id
from ai.backend.common.contexts.user import current_user, triggered_user
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.actions.action import BaseAction, BaseActionTriggerMeta, ProcessResult
from ai.backend.manager.actions.audit_policy import AuditLogPolicy
from ai.backend.manager.actions.monitors.monitor import ActionMonitor
from ai.backend.manager.actions.types import BLANK_ID
from ai.backend.manager.repositories.audit_log import AuditLogRepository
from ai.backend.manager.repositories.audit_log.creators import LegacyAuditLogCreatorSpec
from ai.backend.manager.repositories.base import Creator

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class AuditLogMonitor(ActionMonitor):
    _repository: AuditLogRepository
    _policy: AuditLogPolicy

    def __init__(self, repository: AuditLogRepository, policy: AuditLogPolicy) -> None:
        self._repository = repository
        self._policy = policy

    async def _generate_log(self, action: BaseAction, result: ProcessResult) -> None:
        trigger = triggered_user()
        acting = current_user()
        creator = Creator(
            spec=LegacyAuditLogCreatorSpec(
                action_id=result.meta.action_id,
                entity_type=action.entity_type(),
                operation=action.operation_type(),
                # Legacy actions declare no name; record the spec type until each
                # is replaced by a v2 action that declares one.
                action_name=action.spec().type(),
                created_at=result.meta.started_at,
                description=result.meta.description,
                status=result.meta.status,
                entity_id=result.meta.entity_id,
                request_id=current_request_id() or BLANK_ID,
                triggered_by=str(trigger.user_id) if trigger else None,
                acted_as=acting.user_id if acting else None,
                duration=result.meta.duration,
            )
        )
        await self._repository.create(creator)

    @override
    async def prepare(self, action: BaseAction, meta: BaseActionTriggerMeta) -> None:
        pass

    @override
    async def done(self, action: BaseAction, result: ProcessResult) -> None:
        if not self._policy.should_record(action.spec(), result.meta.status):
            return
        await self._generate_log(action, result)
