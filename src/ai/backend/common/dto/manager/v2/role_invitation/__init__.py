"""
Role invitation DTOs v2 for Manager API.
"""

from ai.backend.common.dto.manager.v2.role_invitation.request import (
    CreateRoleInvitationInput,
    SearchRoleInvitationsInput,
)
from ai.backend.common.dto.manager.v2.role_invitation.response import (
    CreateRoleInvitationPayload,
    RoleInvitationNode,
    SearchRoleInvitationsPayload,
)
from ai.backend.common.dto.manager.v2.role_invitation.types import (
    RoleInvitationStateDTO,
)

__all__ = (
    # Types
    "RoleInvitationStateDTO",
    # Input models (request)
    "CreateRoleInvitationInput",
    "SearchRoleInvitationsInput",
    # Node and Payload models (response)
    "CreateRoleInvitationPayload",
    "RoleInvitationNode",
    "SearchRoleInvitationsPayload",
)
