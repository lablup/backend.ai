from __future__ import annotations

from ai.backend.manager.actions.monitors.monitor import ActionMonitor
from ai.backend.manager.actions.processor import ActionProcessor
from ai.backend.manager.actions.processor.bulk import BulkActionProcessor
from ai.backend.manager.actions.processor.single_entity import SingleEntityActionProcessor
from ai.backend.manager.actions.validators import ActionValidators
from ai.backend.manager.services.idle_checker_assignment.actions.admin_search import (
    AdminSearchIdleCheckerAssignmentsAction,
    AdminSearchIdleCheckerAssignmentsActionResult,
)
from ai.backend.manager.services.idle_checker_assignment.actions.create import (
    CreateIdleCheckerAssignmentAction,
    CreateIdleCheckerAssignmentActionResult,
)
from ai.backend.manager.services.idle_checker_assignment.actions.purge import (
    PurgeIdleCheckerAssignmentAction,
    PurgeIdleCheckerAssignmentActionResult,
)
from ai.backend.manager.services.idle_checker_assignment.actions.scoped_search import (
    ScopedSearchIdleCheckerAssignmentsAction,
    ScopedSearchIdleCheckerAssignmentsActionResult,
)
from ai.backend.manager.services.idle_checker_assignment.actions.update import (
    UpdateIdleCheckerAssignmentAction,
    UpdateIdleCheckerAssignmentActionResult,
)
from ai.backend.manager.services.idle_checker_assignment.service import IdleCheckerAssignmentService


class IdleCheckerAssignmentProcessors:
    create: ActionProcessor[
        CreateIdleCheckerAssignmentAction, CreateIdleCheckerAssignmentActionResult
    ]
    update: SingleEntityActionProcessor[
        UpdateIdleCheckerAssignmentAction, UpdateIdleCheckerAssignmentActionResult
    ]
    purge: SingleEntityActionProcessor[
        PurgeIdleCheckerAssignmentAction, PurgeIdleCheckerAssignmentActionResult
    ]
    admin_search: ActionProcessor[
        AdminSearchIdleCheckerAssignmentsAction, AdminSearchIdleCheckerAssignmentsActionResult
    ]
    scoped_search: BulkActionProcessor[
        ScopedSearchIdleCheckerAssignmentsAction, ScopedSearchIdleCheckerAssignmentsActionResult
    ]

    def __init__(
        self,
        service: IdleCheckerAssignmentService,
        action_monitors: list[ActionMonitor],
        validators: ActionValidators,
    ) -> None:
        # Super-admin gating for create/admin_search happens at the GQL resolver
        # (check_admin_only); update/purge rely on the single-entity RBAC validator.
        self.create = ActionProcessor(service.create, action_monitors)
        self.update = SingleEntityActionProcessor(
            service.update, action_monitors, validators=[validators.rbac.single_entity]
        )
        self.purge = SingleEntityActionProcessor(
            service.purge, action_monitors, validators=[validators.rbac.single_entity]
        )
        self.admin_search = ActionProcessor(service.admin_search, action_monitors)
        self.scoped_search = BulkActionProcessor(
            service.scoped_search,
            monitors=action_monitors,
            validators=[validators.rbac.bulk],
        )
