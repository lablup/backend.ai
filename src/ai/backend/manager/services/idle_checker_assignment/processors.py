from __future__ import annotations

from typing import Any

from ai.backend.manager.actions.registry.group import ProcessorGroup
from ai.backend.manager.actions.v2.global_scope.processor import GlobalActionProcessor
from ai.backend.manager.actions.v2.lookup.processor import LookupActionProcessor
from ai.backend.manager.actions.v2.scope.processor import ScopeActionProcessor
from ai.backend.manager.services.idle_checker_assignment.actions.admin_search import (
    AdminSearchIdleCheckerAssignmentsAction,
    SearchIdleCheckerAssignmentsActionResult,
)
from ai.backend.manager.services.idle_checker_assignment.actions.lookup import (
    LookupIdleCheckerAssignmentAction,
    LookupIdleCheckerAssignmentActionResult,
    LookupIdleCheckerAssignmentByPairAction,
)
from ai.backend.manager.services.idle_checker_assignment.actions.scoped_search import (
    ScopedSearchIdleCheckerAssignmentsAction,
    ScopedSearchIdleCheckerAssignmentsActionResult,
)
from ai.backend.manager.services.idle_checker_assignment.service import IdleCheckerAssignmentService


class IdleCheckerAssignmentProcessors:
    """A binding is a relation between a scope and an idle checker, so its writes go
    through the rbac boundary's relation operations and answer for both sides. What is
    left here reads the binding table, which takes the entity group.
    """

    lookup: LookupActionProcessor[
        LookupIdleCheckerAssignmentAction, LookupIdleCheckerAssignmentActionResult
    ]
    lookup_by_pair: LookupActionProcessor[
        LookupIdleCheckerAssignmentByPairAction, LookupIdleCheckerAssignmentActionResult
    ]
    admin_search: GlobalActionProcessor[
        AdminSearchIdleCheckerAssignmentsAction, SearchIdleCheckerAssignmentsActionResult
    ]
    scoped_search: ScopeActionProcessor[
        ScopedSearchIdleCheckerAssignmentsAction, ScopedSearchIdleCheckerAssignmentsActionResult
    ]

    def __init__(
        self,
        group: ProcessorGroup[Any],
        service: IdleCheckerAssignmentService,
    ) -> None:
        self.lookup = group.lookup(LookupIdleCheckerAssignmentAction, service.lookup)
        self.lookup_by_pair = group.lookup(
            LookupIdleCheckerAssignmentByPairAction, service.lookup_by_pair
        )
        self.admin_search = group.global_scope(
            AdminSearchIdleCheckerAssignmentsAction, service.admin_search
        )
        self.scoped_search = group.scope(
            ScopedSearchIdleCheckerAssignmentsAction, service.scoped_search
        )
