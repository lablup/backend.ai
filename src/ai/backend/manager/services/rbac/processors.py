from __future__ import annotations

from typing import Any

from ai.backend.manager.actions.registry.group import ProcessorGroup
from ai.backend.manager.actions.registry.relation import RelationGroup
from ai.backend.manager.actions.v2.relation.processor import RelationActionProcessor
from ai.backend.manager.actions.v2.scope.processor import ScopeActionProcessor
from ai.backend.manager.data.user.types import UserData
from ai.backend.manager.services.rbac.actions.relation.create import (
    CreateRelationAction,
    CreateRelationActionResult,
)
from ai.backend.manager.services.rbac.actions.relation.purge import (
    PurgeRelationAction,
    PurgeRelationActionResult,
)
from ai.backend.manager.services.rbac.actions.roster.join_project import (
    JoinProjectAction,
    JoinProjectActionResult,
)
from ai.backend.manager.services.rbac.actions.roster.leave_project import (
    LeaveProjectAction,
    LeaveProjectActionResult,
)
from ai.backend.manager.services.rbac.service import RbacRelationService, RbacRosterService

__all__ = ("RbacProcessors",)


class RbacProcessors:
    """The graph this system writes: the links between two entities, and who is on a
    project's roster.

    One wiring per direction covers every relation — the spec travels on the action, and
    which pairs a run named are on its scopes. A run carries as many pairs as the request
    named, so a caller never loops over the service. A relation asks the permission of
    every scope it names, so a caller reaching one side alone gets nothing. A roster
    place asks the ``user`` permission at the project, the one scope a user inside a
    project is in.
    """

    create_relation: RelationActionProcessor[
        CreateRelationAction[Any, Any, Any], CreateRelationActionResult[Any, Any]
    ]
    purge_relation: RelationActionProcessor[
        PurgeRelationAction[Any, Any, Any], PurgeRelationActionResult[Any, Any]
    ]
    join_project: ScopeActionProcessor[JoinProjectAction, JoinProjectActionResult]
    leave_project: ScopeActionProcessor[LeaveProjectAction, LeaveProjectActionResult]

    def __init__(
        self,
        group: RelationGroup,
        roster_group: ProcessorGroup[UserData],
        service: RbacRelationService,
        roster_service: RbacRosterService,
    ) -> None:
        self.create_relation = group.relation(CreateRelationAction, service.create)
        self.purge_relation = group.relation(PurgeRelationAction, service.purge)
        self.join_project = roster_group.scope(JoinProjectAction, roster_service.join)
        self.leave_project = roster_group.scope(LeaveProjectAction, roster_service.leave)
