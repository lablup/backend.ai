from ai.backend.manager.actions.monitors.monitor import ActionMonitor
from ai.backend.manager.actions.processor.global_action import GlobalActionProcessor
from ai.backend.manager.services.idle_checker.actions.admin_search import (
    AdminSearchIdleCheckersAction,
    SearchIdleCheckersActionResult,
)
from ai.backend.manager.services.idle_checker.actions.create import (
    CreateIdleCheckerAction,
    CreateIdleCheckerActionResult,
)
from ai.backend.manager.services.idle_checker.actions.purge import (
    PurgeIdleCheckerAction,
    PurgeIdleCheckerActionResult,
)
from ai.backend.manager.services.idle_checker.actions.update import (
    UpdateIdleCheckerAction,
    UpdateIdleCheckerActionResult,
)
from ai.backend.manager.services.idle_checker.service import IdleCheckerService


class IdleCheckerProcessors:
    admin_search: GlobalActionProcessor[
        AdminSearchIdleCheckersAction,
        SearchIdleCheckersActionResult,
    ]
    create: GlobalActionProcessor[CreateIdleCheckerAction, CreateIdleCheckerActionResult]
    update: GlobalActionProcessor[UpdateIdleCheckerAction, UpdateIdleCheckerActionResult]
    purge: GlobalActionProcessor[PurgeIdleCheckerAction, PurgeIdleCheckerActionResult]

    def __init__(
        self,
        service: IdleCheckerService,
        action_monitors: list[ActionMonitor],
    ) -> None:
        self.admin_search = GlobalActionProcessor(service.admin_search, action_monitors)
        self.create = GlobalActionProcessor(service.create, action_monitors)
        self.update = GlobalActionProcessor(service.update, action_monitors)
        self.purge = GlobalActionProcessor(service.purge, action_monitors)
