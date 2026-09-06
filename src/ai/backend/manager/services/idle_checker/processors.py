from ai.backend.manager.actions.monitors.monitor import ActionMonitor
from ai.backend.manager.actions.processor.global_action import GlobalActionProcessor
from ai.backend.manager.actions.registry.group import ProcessorGroup
from ai.backend.manager.actions.v2.bulk.processor import BulkActionProcessor
from ai.backend.manager.data.session.types import SessionData
from ai.backend.manager.services.idle_checker.actions.admin_search import (
    AdminSearchIdleCheckersAction,
    SearchIdleCheckersActionResult,
)
from ai.backend.manager.services.idle_checker.actions.create import (
    CreateIdleCheckerAction,
    CreateIdleCheckerActionResult,
)
from ai.backend.manager.services.idle_checker.actions.exclude_sessions import (
    ExcludeSessionIdleChecksAction,
    ExcludeSessionIdleChecksActionResult,
)
from ai.backend.manager.services.idle_checker.actions.include_sessions import (
    IncludeSessionIdleChecksAction,
    IncludeSessionIdleChecksActionResult,
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
    exclude_sessions: BulkActionProcessor[
        ExcludeSessionIdleChecksAction,
        ExcludeSessionIdleChecksActionResult,
    ]
    include_sessions: BulkActionProcessor[
        IncludeSessionIdleChecksAction,
        IncludeSessionIdleChecksActionResult,
    ]

    def __init__(
        self,
        group: ProcessorGroup[SessionData],
        service: IdleCheckerService,
        action_monitors: list[ActionMonitor],
    ) -> None:
        self.admin_search = GlobalActionProcessor(service.admin_search, action_monitors)
        self.create = GlobalActionProcessor(service.create, action_monitors)
        self.update = GlobalActionProcessor(service.update, action_monitors)
        self.purge = GlobalActionProcessor(service.purge, action_monitors)
        self.exclude_sessions = group.legacy_partial_bulk(
            ExcludeSessionIdleChecksAction, service.exclude_sessions
        )
        self.include_sessions = group.legacy_partial_bulk(
            IncludeSessionIdleChecksAction, service.include_sessions
        )
