from typing import override

from ai.backend.common.contexts.request_id import current_request_id
from ai.backend.common.contexts.user import current_user, triggered_user
from ai.backend.manager.actions.action import BaseActionTriggerMeta
from ai.backend.manager.actions.single_entity.base import BaseSingleEntityAction
from ai.backend.manager.actions.single_entity.monitor.base import SingleEntityActionMonitor
from ai.backend.manager.actions.single_entity.result import SingleEntityActionProcessResult
from ai.backend.manager.actions.types import BLANK_ID
from ai.backend.manager.repositories.audit_log import AuditLogCreatorSpec, AuditLogRepository
from ai.backend.manager.repositories.base import Creator

__all__ = ("SingleEntityAuditLogMonitor",)


class SingleEntityAuditLogMonitor(SingleEntityActionMonitor):
    _repository: AuditLogRepository

    def __init__(self, repository: AuditLogRepository) -> None:
        self._repository = repository

    async def _generate_log(
        self, action: BaseSingleEntityAction, result: SingleEntityActionProcessResult
    ) -> None:
        trigger = triggered_user()
        acting = current_user()
        creator = Creator(
            spec=AuditLogCreatorSpec(
                action_id=result.meta.action_id,
                entity_type=action.entity_type(),
                operation=action.operation_type(),
                created_at=result.meta.started_at,
                description=result.meta.description,
                status=result.meta.status,
                entity_id=str(result.meta.entity_id),
                request_id=current_request_id() or BLANK_ID,
                triggered_by=str(trigger.user_id) if trigger else None,
                acted_as=acting.user_id if acting else None,
                duration=result.meta.duration,
            )
        )
        await self._repository.create(creator)

    @override
    async def prepare(self, action: BaseSingleEntityAction, meta: BaseActionTriggerMeta) -> None:
        pass

    @override
    async def done(
        self, action: BaseSingleEntityAction, result: SingleEntityActionProcessResult
    ) -> None:
        await self._generate_log(action, result)
