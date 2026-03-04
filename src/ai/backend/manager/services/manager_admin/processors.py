from __future__ import annotations

from typing import override

from ai.backend.manager.actions.monitors.monitor import ActionMonitor
from ai.backend.manager.actions.processor import ActionProcessor
from ai.backend.manager.actions.types import AbstractProcessorPackage, ActionSpec
from ai.backend.manager.actions.validators import ActionValidators

from .actions.fetch_status import FetchManagerStatusAction, FetchManagerStatusActionResult
from .actions.get_announcement import GetAnnouncementAction, GetAnnouncementActionResult
from .actions.get_db_cxn_status import GetDbCxnStatusAction, GetDbCxnStatusActionResult
from .actions.perform_scheduler_ops import (
    PerformSchedulerOpsAction,
    PerformSchedulerOpsActionResult,
)
from .actions.update_announcement import UpdateAnnouncementAction, UpdateAnnouncementActionResult
from .actions.update_status import UpdateManagerStatusAction, UpdateManagerStatusActionResult
from .service import ManagerAdminService

__all__ = ("ManagerAdminProcessors",)


class ManagerAdminProcessors(AbstractProcessorPackage):
    """Processor package for manager admin operations."""

    fetch_status: ActionProcessor[FetchManagerStatusAction, FetchManagerStatusActionResult]
    update_status: ActionProcessor[UpdateManagerStatusAction, UpdateManagerStatusActionResult]
    get_announcement: ActionProcessor[GetAnnouncementAction, GetAnnouncementActionResult]
    update_announcement: ActionProcessor[UpdateAnnouncementAction, UpdateAnnouncementActionResult]
    perform_scheduler_ops: ActionProcessor[
        PerformSchedulerOpsAction, PerformSchedulerOpsActionResult
    ]
    get_db_cxn_status: ActionProcessor[GetDbCxnStatusAction, GetDbCxnStatusActionResult]

    def __init__(
        self,
        service: ManagerAdminService,
        action_monitors: list[ActionMonitor],
        validators: ActionValidators,
    ) -> None:
        self.fetch_status = ActionProcessor(service.fetch_status, action_monitors)
        self.update_status = ActionProcessor(service.update_status, action_monitors)
        self.get_announcement = ActionProcessor(service.get_announcement, action_monitors)
        self.update_announcement = ActionProcessor(service.update_announcement, action_monitors)
        self.perform_scheduler_ops = ActionProcessor(service.perform_scheduler_ops, action_monitors)
        self.get_db_cxn_status = ActionProcessor(service.get_db_cxn_status, action_monitors)

    @override
    def supported_actions(self) -> list[ActionSpec]:
        return [
            FetchManagerStatusAction.spec(),
            UpdateManagerStatusAction.spec(),
            GetAnnouncementAction.spec(),
            UpdateAnnouncementAction.spec(),
            PerformSchedulerOpsAction.spec(),
            GetDbCxnStatusAction.spec(),
        ]
