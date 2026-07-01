"""RBAC action declarations for role invitation operations.

Each class is both an RBAC permission declaration (registered in
RBAC_ACTION_REGISTRY) and a data-carrying action that the service layer
receives.
"""

from dataclasses import dataclass, field
from typing import override
from uuid import UUID

from ai.backend.common.data.permission.types import OperationType, RBACElementType
from ai.backend.manager.actions.action.rbac import (
    BaseRBACAction,
    RBACActionName,
    RBACRequiredPermission,
)
from ai.backend.manager.data.role_invitation.types import RoleInvitationData


@dataclass
class CreateRoleInvitationByEmailAction(BaseRBACAction):
    """Project admin creates role invitations by invitee emails."""

    invitee_emails: list[str]
    inviter_user_id: UUID
    role_id: UUID

    @classmethod
    @override
    def action_name(cls) -> RBACActionName:
        return RBACActionName.CREATE

    @classmethod
    @override
    def required_permission(cls) -> RBACRequiredPermission:
        return RBACRequiredPermission(RBACElementType.ROLE_ASSIGNMENT, OperationType.CREATE)

    @classmethod
    @override
    def permission_scope(cls) -> RBACElementType:
        return RBACElementType.PROJECT


@dataclass
class CreateRoleInvitationResult:
    """Result of creating role invitations."""

    created: list[RoleInvitationData] = field(default_factory=list)


class RoleInvitationReadRBACAction(BaseRBACAction):
    """Read / search role invitations."""

    @classmethod
    @override
    def action_name(cls) -> RBACActionName:
        return RBACActionName.SEARCH

    @classmethod
    @override
    def required_permission(cls) -> RBACRequiredPermission:
        return RBACRequiredPermission(RBACElementType.ROLE_ASSIGNMENT, OperationType.READ)

    @classmethod
    @override
    def permission_scope(cls) -> RBACElementType:
        return RBACElementType.PROJECT


@dataclass
class AcceptRoleInvitationAction(BaseRBACAction):
    """Invitee accepts a role invitation."""

    invitation_id: UUID

    @classmethod
    @override
    def action_name(cls) -> RBACActionName:
        return RBACActionName.UPDATE

    @classmethod
    @override
    def required_permission(cls) -> RBACRequiredPermission:
        return RBACRequiredPermission(RBACElementType.ROLE_ASSIGNMENT, OperationType.UPDATE)

    @classmethod
    @override
    def permission_scope(cls) -> RBACElementType:
        return RBACElementType.USER


@dataclass
class RejectRoleInvitationAction(BaseRBACAction):
    """Invitee rejects a role invitation."""

    invitation_id: UUID

    @classmethod
    @override
    def action_name(cls) -> RBACActionName:
        return RBACActionName.UPDATE

    @classmethod
    @override
    def required_permission(cls) -> RBACRequiredPermission:
        return RBACRequiredPermission(RBACElementType.ROLE_ASSIGNMENT, OperationType.UPDATE)

    @classmethod
    @override
    def permission_scope(cls) -> RBACElementType:
        return RBACElementType.USER


@dataclass
class CancelRoleInvitationAction(BaseRBACAction):
    """Project admin cancels a role invitation."""

    invitation_id: UUID

    @classmethod
    @override
    def action_name(cls) -> RBACActionName:
        return RBACActionName.SOFT_DELETE

    @classmethod
    @override
    def required_permission(cls) -> RBACRequiredPermission:
        return RBACRequiredPermission(RBACElementType.ROLE_ASSIGNMENT, OperationType.SOFT_DELETE)

    @classmethod
    @override
    def permission_scope(cls) -> RBACElementType:
        return RBACElementType.PROJECT
