from __future__ import annotations

from typing import Any

from ai.backend.manager.actions.monitors.monitor import ActionMonitor
from ai.backend.manager.actions.processor import ActionProcessor
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
from ai.backend.manager.services.rbac.actions.relation.switch import (
    DeleteRelationAction,
    DeleteRelationActionResult,
    RestoreRelationAction,
    RestoreRelationActionResult,
)
from ai.backend.manager.services.rbac.actions.role.assign import (
    AssignRoleAction,
    AssignRoleActionResult,
)
from ai.backend.manager.services.rbac.actions.role.bulk_assign import (
    BulkAssignRoleAction,
    BulkAssignRoleActionResult,
)
from ai.backend.manager.services.rbac.actions.role.bulk_revoke import (
    BulkRevokeRoleAction,
    BulkRevokeRoleActionResult,
)
from ai.backend.manager.services.rbac.actions.role.revoke import (
    RevokeRoleAction,
    RevokeRoleActionResult,
)
from ai.backend.manager.services.rbac.actions.roster.join_project import (
    JoinProjectAction,
    JoinProjectActionResult,
)
from ai.backend.manager.services.rbac.actions.roster.leave_project import (
    LeaveProjectAction,
    LeaveProjectActionResult,
)
from ai.backend.manager.services.rbac.service import (
    RbacRelationService,
    RbacRoleService,
    RbacRosterService,
)

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

    Granting a role and taking it back sit here too: each writes a roster place beside
    the role row, and the two have to land together.
    """

    create_relation: RelationActionProcessor[
        CreateRelationAction[Any, Any, Any], CreateRelationActionResult[Any, Any]
    ]
    purge_relation: RelationActionProcessor[
        PurgeRelationAction[Any, Any, Any], PurgeRelationActionResult[Any, Any]
    ]
    delete_relation: RelationActionProcessor[
        DeleteRelationAction[Any, Any, Any], DeleteRelationActionResult[Any, Any]
    ]
    restore_relation: RelationActionProcessor[
        RestoreRelationAction[Any, Any, Any], RestoreRelationActionResult[Any, Any]
    ]
    join_project: ScopeActionProcessor[JoinProjectAction, JoinProjectActionResult]
    leave_project: ScopeActionProcessor[LeaveProjectAction, LeaveProjectActionResult]
    assign_role: ActionProcessor[AssignRoleAction, AssignRoleActionResult]
    revoke_role: ActionProcessor[RevokeRoleAction, RevokeRoleActionResult]
    bulk_assign_role: ActionProcessor[BulkAssignRoleAction, BulkAssignRoleActionResult]
    bulk_revoke_role: ActionProcessor[BulkRevokeRoleAction, BulkRevokeRoleActionResult]

    def __init__(
        self,
        group: RelationGroup,
        roster_group: ProcessorGroup[UserData],
        service: RbacRelationService,
        roster_service: RbacRosterService,
        role_service: RbacRoleService,
        action_monitors: list[ActionMonitor],
    ) -> None:
        self.create_relation = group.relation(CreateRelationAction, service.create)
        self.purge_relation = group.relation(PurgeRelationAction, service.purge)
        self.delete_relation = group.relation(DeleteRelationAction, service.delete)
        self.restore_relation = group.relation(RestoreRelationAction, service.restore)
        self.join_project = roster_group.scope(JoinProjectAction, roster_service.join)
        self.leave_project = roster_group.scope(LeaveProjectAction, roster_service.leave)
        self.assign_role = ActionProcessor(role_service.assign_role, action_monitors)
        self.revoke_role = ActionProcessor(role_service.revoke_role, action_monitors)
        self.bulk_assign_role = ActionProcessor(role_service.bulk_assign_role, action_monitors)
        self.bulk_revoke_role = ActionProcessor(role_service.bulk_revoke_role, action_monitors)
