"""Service-layer actions for role invitation operations.

Scope mapping:
- create, my_search, role_search → ``BaseScopeAction`` with ``ScopeActionRBACValidator``
- accept, reject, cancel        → ``BaseSingleEntityAction`` with ``SingleEntityActionRBACValidator``
"""

from dataclasses import dataclass
from typing import override
from uuid import UUID

from ai.backend.common.data.permission.types import EntityType, RBACElementType, ScopeType
from ai.backend.manager.actions.action import BaseAction, BaseActionResult
from ai.backend.manager.actions.action.scope import BaseScopeAction, BaseScopeActionResult
from ai.backend.manager.actions.action.single_entity import (
    BaseSingleEntityAction,
    BaseSingleEntityActionResult,
)
from ai.backend.manager.actions.action.types import FieldData
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.common.types import SearchResult
from ai.backend.manager.data.permission.types import RBACElementRef
from ai.backend.manager.data.role_invitation.types import RoleInvitationData
from ai.backend.manager.repositories.base import BatchQuerier
from ai.backend.manager.repositories.role_invitation.types import (
    InviteeSearchScope,
    InviterSearchScope,
    RoleInvitationSearchScope,
)

# ------------------------------------------------------------------ scope base (create, search)


@dataclass
class _RoleScopedInvitationAction(BaseScopeAction):
    """Base for actions scoped to a ROLE (create, role_search)."""

    role_id: UUID

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return EntityType.ROLE_ASSIGNMENT

    @override
    def scope_type(self) -> ScopeType:
        return ScopeType.ROLE

    @override
    def scope_id(self) -> str:
        return str(self.role_id)

    @override
    def target_element(self) -> RBACElementRef:
        return RBACElementRef(RBACElementType.ROLE, str(self.role_id))


@dataclass
class _UserScopedInvitationAction(BaseScopeAction):
    """Base for actions scoped to a USER (my_search)."""

    user_id: UUID

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return EntityType.ROLE_ASSIGNMENT

    @override
    def scope_type(self) -> ScopeType:
        return ScopeType.USER

    @override
    def scope_id(self) -> str:
        return str(self.user_id)

    @override
    def target_element(self) -> RBACElementRef:
        return RBACElementRef(RBACElementType.USER, str(self.user_id))


class _InvitationScopeActionResult(BaseScopeActionResult):
    @override
    def scope_type(self) -> ScopeType:
        return ScopeType.ROLE

    @override
    def scope_id(self) -> str:
        return ""


# ------------------------------------------------------------------ single entity base (accept, reject, cancel)


@dataclass
class _InvitationSingleEntityAction(BaseSingleEntityAction):
    """Base for actions targeting a specific invitation."""

    invitation_id: UUID

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return EntityType.ROLE_ASSIGNMENT

    @override
    def target_entity_id(self) -> str:
        return str(self.invitation_id)

    @override
    def target_element(self) -> RBACElementRef:
        return RBACElementRef(RBACElementType.ROLE_ASSIGNMENT, str(self.invitation_id))

    @override
    def field_data(self) -> FieldData | None:
        return None


class _InvitationSingleEntityActionResult(BaseSingleEntityActionResult):
    pass


# ------------------------------------------------------------------ create


@dataclass
class CreateRoleInvitationAction(_RoleScopedInvitationAction):
    """Create role invitations by email."""

    invitee_emails: list[str]
    inviter_user_id: UUID

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.CREATE


@dataclass
class CreateRoleInvitationActionResult(_InvitationScopeActionResult):
    created: list[RoleInvitationData]

    @override
    def entity_id(self) -> str | None:
        return None


# ------------------------------------------------------------------ accept / reject / cancel


@dataclass
class AcceptRoleInvitationAction(_InvitationSingleEntityAction):
    """Invitee accepts a pending invitation."""

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE


@dataclass
class RejectRoleInvitationAction(_InvitationSingleEntityAction):
    """Invitee rejects a pending invitation."""

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE


@dataclass
class CancelRoleInvitationAction(_InvitationSingleEntityAction):
    """Admin cancels a pending invitation."""

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.DELETE


@dataclass
class RoleInvitationActionResult(_InvitationSingleEntityActionResult):
    """Result wrapping a single RoleInvitationData."""

    data: RoleInvitationData

    @override
    def target_entity_id(self) -> str:
        return str(self.data.id)


# ------------------------------------------------------------------ my_search


@dataclass
class SearchMyRoleInvitationsAction(_UserScopedInvitationAction):
    """Search invitations addressed to the current user."""

    querier: BatchQuerier
    scope: InviteeSearchScope

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH


@dataclass
class SearchMyRoleInvitationsActionResult(_InvitationScopeActionResult):
    result: SearchResult[RoleInvitationData]

    @override
    def entity_id(self) -> str | None:
        return None


# ------------------------------------------------------------------ my_sent_search


@dataclass
class SearchMySentRoleInvitationsAction(_UserScopedInvitationAction):
    """Search invitations sent by the current user."""

    querier: BatchQuerier
    scope: InviterSearchScope

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH


@dataclass
class SearchMySentRoleInvitationsActionResult(_InvitationScopeActionResult):
    result: SearchResult[RoleInvitationData]

    @override
    def entity_id(self) -> str | None:
        return None


# ------------------------------------------------------------------ role_search (no RBAC validator)


@dataclass
class SearchRoleInvitationsByRoleAction(_RoleScopedInvitationAction):
    """Search invitations by role (admin/project-admin view)."""

    querier: BatchQuerier
    scope: RoleInvitationSearchScope

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH


@dataclass
class SearchRoleInvitationsByRoleActionResult(_InvitationScopeActionResult):
    result: SearchResult[RoleInvitationData]

    @override
    def entity_id(self) -> str | None:
        return None


# ------------------------------------------------------------------ admin_search (no scope, superadmin only)


@dataclass
class AdminSearchRoleInvitationsAction(BaseAction):
    """Search all invitations across the system (superadmin only)."""

    querier: BatchQuerier

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return EntityType.ROLE_ASSIGNMENT

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH


@dataclass
class AdminSearchRoleInvitationsActionResult(BaseActionResult):
    result: SearchResult[RoleInvitationData]

    @override
    def entity_id(self) -> str | None:
        return None
