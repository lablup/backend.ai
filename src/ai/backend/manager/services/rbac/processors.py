from __future__ import annotations

from typing import Any

from ai.backend.manager.actions.registry.group import ProcessorGroup
from ai.backend.manager.actions.registry.relation import RelationGroup
from ai.backend.manager.actions.v2.relation.processor import RelationActionProcessor
from ai.backend.manager.actions.v2.scope.processor import ScopeActionProcessor
from ai.backend.manager.services.rbac.actions.create_relation import (
    CreateRelationAction,
    CreateRelationActionResult,
)
from ai.backend.manager.services.rbac.actions.delete_relation import (
    DeleteRelationAction,
    DeleteRelationActionResult,
)
from ai.backend.manager.services.rbac.actions.enroll import EnrollAction, EnrollActionResult
from ai.backend.manager.services.rbac.actions.grant_roles import (
    GrantRolesAction,
    GrantRolesActionResult,
)
from ai.backend.manager.services.rbac.actions.purge_relation import (
    PurgeRelationAction,
    PurgeRelationActionResult,
)
from ai.backend.manager.services.rbac.actions.restore_relation import (
    RestoreRelationAction,
    RestoreRelationActionResult,
)
from ai.backend.manager.services.rbac.actions.revoke_roles import (
    RevokeRolesAction,
    RevokeRolesActionResult,
)
from ai.backend.manager.services.rbac.actions.withdraw import (
    WithdrawAction,
    WithdrawActionResult,
)
from ai.backend.manager.services.rbac.service import RBACService


class RBACProcessors:
    """One wiring per operation, whichever table the run writes.

    The spec is a value on the action, so a domain reaches these by naming its own
    spec rather than by wiring a processor of its own. What the run was about is the
    scopes it names, which is what the audit trail records.

    The four relation operations are answered for by both scopes and by no entity type,
    which is why they come from a group of their own. The four membership ones are
    answered for by the organization, with the member as the entity acted on inside it.
    """

    create_relation: RelationActionProcessor[CreateRelationAction[Any], CreateRelationActionResult]
    delete_relation: RelationActionProcessor[DeleteRelationAction[Any], DeleteRelationActionResult]
    restore_relation: RelationActionProcessor[
        RestoreRelationAction[Any], RestoreRelationActionResult
    ]
    purge_relation: RelationActionProcessor[PurgeRelationAction[Any], PurgeRelationActionResult]
    enroll: ScopeActionProcessor[EnrollAction[Any], EnrollActionResult]
    withdraw: ScopeActionProcessor[WithdrawAction[Any], WithdrawActionResult]
    grant_roles: ScopeActionProcessor[GrantRolesAction, GrantRolesActionResult]
    revoke_roles: ScopeActionProcessor[RevokeRolesAction, RevokeRolesActionResult]

    def __init__(
        self,
        relation_group: RelationGroup,
        member_group: ProcessorGroup[Any],
        service: RBACService,
    ) -> None:
        self.create_relation = relation_group.relation(
            CreateRelationAction, service.create_relation
        )
        self.delete_relation = relation_group.relation(
            DeleteRelationAction, service.delete_relation
        )
        self.restore_relation = relation_group.relation(
            RestoreRelationAction, service.restore_relation
        )
        self.purge_relation = relation_group.relation(PurgeRelationAction, service.purge_relation)
        self.enroll = member_group.scope(EnrollAction, service.enroll)
        self.withdraw = member_group.scope(WithdrawAction, service.withdraw)
        self.grant_roles = member_group.scope(GrantRolesAction, service.grant_roles)
        self.revoke_roles = member_group.scope(RevokeRolesAction, service.revoke_roles)
