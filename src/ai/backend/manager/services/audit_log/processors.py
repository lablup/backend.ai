from __future__ import annotations

from typing import override

from ai.backend.manager.actions.monitors.monitor import ActionMonitor
from ai.backend.manager.actions.processor import ActionProcessor
from ai.backend.manager.actions.types import AbstractProcessorPackage, ActionSpec
from ai.backend.manager.services.audit_log.actions.create import (
    CreateAuditLogAction,
    CreateAuditLogActionResult,
)
from ai.backend.manager.services.audit_log.actions.search import (
    SearchAuditLogsAction,
    SearchAuditLogsActionResult,
)
from ai.backend.manager.services.audit_log.service import AuditLogService


class AuditLogProcessors(AbstractProcessorPackage):
    create: ActionProcessor[CreateAuditLogAction, CreateAuditLogActionResult]
    search: ActionProcessor[SearchAuditLogsAction, SearchAuditLogsActionResult]

    def __init__(self, service: AuditLogService, action_monitors: list[ActionMonitor]) -> None:
        self.create = ActionProcessor(service.create, action_monitors)
        self.search = ActionProcessor(service.search, action_monitors)

    @override
    def supported_actions(self) -> list[ActionSpec]:
        return [
            CreateAuditLogAction.spec(),
            SearchAuditLogsAction.spec(),
        ]
