from __future__ import annotations

from typing import Any

from ai.backend.manager.actions.registry import ProcessorGroup
from ai.backend.manager.actions.v2.global_scope.processor import GlobalActionProcessor
from ai.backend.manager.services.manager_admin.actions.fetch_status import (
    FetchManagerStatusAction,
    FetchManagerStatusActionResult,
)
from ai.backend.manager.services.manager_admin.actions.get_announcement import (
    GetAnnouncementAction,
    GetAnnouncementActionResult,
)
from ai.backend.manager.services.manager_admin.actions.get_db_cxn_status import (
    GetDbCxnStatusAction,
    GetDbCxnStatusActionResult,
)
from ai.backend.manager.services.manager_admin.actions.perform_scheduler_ops import (
    PerformSchedulerOpsAction,
    PerformSchedulerOpsActionResult,
)
from ai.backend.manager.services.manager_admin.actions.update_announcement import (
    UpdateAnnouncementAction,
    UpdateAnnouncementActionResult,
)
from ai.backend.manager.services.manager_admin.actions.update_status import (
    UpdateManagerStatusAction,
    UpdateManagerStatusActionResult,
)
from ai.backend.manager.services.manager_admin.service import ManagerAdminService


class ManagerAdminProcessors:
    """The manager's own state — its status, its announcement, its scheduler.

    None of it belongs to an entity and all of it reaches etcd or the scheduler, so every
    operation is global and the service stays.
    """

    fetch_status: GlobalActionProcessor[FetchManagerStatusAction, FetchManagerStatusActionResult]
    update_status: GlobalActionProcessor[UpdateManagerStatusAction, UpdateManagerStatusActionResult]
    get_announcement: GlobalActionProcessor[GetAnnouncementAction, GetAnnouncementActionResult]
    update_announcement: GlobalActionProcessor[
        UpdateAnnouncementAction, UpdateAnnouncementActionResult
    ]
    perform_scheduler_ops: GlobalActionProcessor[
        PerformSchedulerOpsAction, PerformSchedulerOpsActionResult
    ]
    get_db_cxn_status: GlobalActionProcessor[GetDbCxnStatusAction, GetDbCxnStatusActionResult]

    def __init__(self, group: ProcessorGroup[Any], service: ManagerAdminService) -> None:
        self.fetch_status = group.global_scope(FetchManagerStatusAction, service.fetch_status)
        self.update_status = group.global_scope(UpdateManagerStatusAction, service.update_status)
        self.get_announcement = group.global_scope(GetAnnouncementAction, service.get_announcement)
        self.update_announcement = group.global_scope(
            UpdateAnnouncementAction, service.update_announcement
        )
        self.perform_scheduler_ops = group.global_scope(
            PerformSchedulerOpsAction, service.perform_scheduler_ops
        )
        self.get_db_cxn_status = group.global_scope(GetDbCxnStatusAction, service.get_db_cxn_status)
