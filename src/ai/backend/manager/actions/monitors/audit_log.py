from __future__ import annotations

import logging
from typing import override

from ai.backend.common.contexts.client_ip import current_client_ip
from ai.backend.common.contexts.request_id import current_request_id
from ai.backend.common.contexts.user import current_user, triggered_user
from ai.backend.common.data.entity.types import EntityType
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.actions.action import BaseAction, BaseActionTriggerMeta, ProcessResult
from ai.backend.manager.actions.audit_policy import AuditLogPolicy
from ai.backend.manager.actions.monitors.monitor import ActionMonitor
from ai.backend.manager.actions.types import BLANK_ID
from ai.backend.manager.data.audit_log.types import AuditLogData
from ai.backend.manager.data.client_ip.masking import ClientIPMaskingTarget
from ai.backend.manager.models.audit_log.creators import LegacyAuditLogCreator
from ai.backend.manager.repositories.client_ip_masking.repository import (
    ClientIPMaskingRepository,
)
from ai.backend.manager.repositories.ops.repository import OpsRepository

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class AuditLogMonitor(ActionMonitor):
    _repository: OpsRepository[AuditLogData]
    _policy: AuditLogPolicy
    _client_ip_masking: ClientIPMaskingRepository

    def __init__(
        self,
        repository: OpsRepository[AuditLogData],
        policy: AuditLogPolicy,
        client_ip_masking: ClientIPMaskingRepository,
    ) -> None:
        self._repository = repository
        self._policy = policy
        self._client_ip_masking = client_ip_masking

    async def _generate_log(self, action: BaseAction, result: ProcessResult) -> None:
        trigger = triggered_user()
        acting = current_user()
        client_ip = await self._client_ip_masking.mask(
            ClientIPMaskingTarget.AUDIT_LOGS, current_client_ip()
        )
        creator = LegacyAuditLogCreator(
            action_id=result.meta.action_id,
            operation=action.operation_type(),
            # Legacy actions declare no name; record the spec type until each
            # is replaced by a v2 action that declares one.
            action_name=action.spec().type(),
            created_at=result.meta.started_at,
            description=result.meta.description,
            status=result.meta.status,
            request_id=current_request_id() or BLANK_ID,
            triggered_by=str(trigger.user_id) if trigger else None,
            acted_as=acting.user_id if acting else None,
            duration=result.meta.duration,
            client_ip=client_ip,
        )
        await self._repository.create_dangling_field(EntityType(action.entity_type()), creator)

    @override
    async def prepare(self, action: BaseAction, meta: BaseActionTriggerMeta) -> None:
        pass

    @override
    async def done(self, action: BaseAction, result: ProcessResult) -> None:
        if not self._policy.should_record(action.operation_type(), result.meta.status):
            return
        await self._generate_log(action, result)
