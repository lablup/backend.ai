from __future__ import annotations

from typing import Any

from ai.backend.manager.actions.registry.group import ProcessorGroup
from ai.backend.manager.actions.registry.relation import RelationGroup
from ai.backend.manager.actions.v2.global_scope.processor import GlobalActionProcessor
from ai.backend.manager.actions.v2.lookup.processor import LookupActionProcessor
from ai.backend.manager.actions.v2.relation.processor import RelationActionProcessor
from ai.backend.manager.actions.v2.scope.processor import ScopeActionProcessor
from ai.backend.manager.data.idle_checker.types import IdleCheckerAssignmentData
from ai.backend.manager.services.idle_checker_assignment.actions.admin_search import (
    AdminSearchIdleCheckerAssignmentsAction,
    SearchIdleCheckerAssignmentsActionResult,
)
from ai.backend.manager.services.idle_checker_assignment.actions.create import (
    CreateIdleCheckerAssignmentAction,
)
from ai.backend.manager.services.idle_checker_assignment.actions.lookup import (
    LookupIdleCheckerAssignmentAction,
    LookupIdleCheckerAssignmentActionResult,
)
from ai.backend.manager.services.idle_checker_assignment.actions.purge import (
    PurgeIdleCheckerAssignmentAction,
)
from ai.backend.manager.services.idle_checker_assignment.actions.scoped_search import (
    ScopedSearchIdleCheckerAssignmentsAction,
    ScopedSearchIdleCheckerAssignmentsActionResult,
)
from ai.backend.manager.services.idle_checker_assignment.actions.update import (
    DisableIdleCheckerAssignmentAction,
    EnableIdleCheckerAssignmentAction,
)
from ai.backend.manager.services.idle_checker_assignment.service import IdleCheckerAssignmentService


class IdleCheckerAssignmentProcessors:
    """A binding is a relation between a scope and an idle checker, so its writes are
    wired through the relation group and answer for both sides. The reads and the id
    resolution name the binding table, so they take the entity group.
    """

    lookup: LookupActionProcessor[
        LookupIdleCheckerAssignmentAction, LookupIdleCheckerAssignmentActionResult
    ]
    create: RelationActionProcessor[CreateIdleCheckerAssignmentAction, IdleCheckerAssignmentData]
    enable: RelationActionProcessor[EnableIdleCheckerAssignmentAction, IdleCheckerAssignmentData]
    disable: RelationActionProcessor[DisableIdleCheckerAssignmentAction, IdleCheckerAssignmentData]
    purge: RelationActionProcessor[PurgeIdleCheckerAssignmentAction, None]
    admin_search: GlobalActionProcessor[
        AdminSearchIdleCheckerAssignmentsAction, SearchIdleCheckerAssignmentsActionResult
    ]
    scoped_search: ScopeActionProcessor[
        ScopedSearchIdleCheckerAssignmentsAction, ScopedSearchIdleCheckerAssignmentsActionResult
    ]

    def __init__(
        self,
        group: ProcessorGroup[Any],
        relations: RelationGroup,
        service: IdleCheckerAssignmentService,
    ) -> None:
        self.lookup = group.lookup(LookupIdleCheckerAssignmentAction, service.lookup)
        self.create = relations.relation(CreateIdleCheckerAssignmentAction, service.create)
        self.enable = relations.relation(EnableIdleCheckerAssignmentAction, service.enable)
        self.disable = relations.relation(DisableIdleCheckerAssignmentAction, service.disable)
        self.purge = relations.relation(PurgeIdleCheckerAssignmentAction, service.purge)
        self.admin_search = group.global_scope(
            AdminSearchIdleCheckerAssignmentsAction, service.admin_search
        )
        self.scoped_search = group.scope(
            ScopedSearchIdleCheckerAssignmentsAction, service.scoped_search
        )
