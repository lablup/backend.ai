"""CreatorSpec implementations for role invitation repository."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override
from uuid import UUID

from ai.backend.manager.data.role_invitation.types import RoleInvitationState
from ai.backend.manager.errors.repository import UniqueConstraintViolationError
from ai.backend.manager.errors.role_invitation import DuplicateRoleInvitationError
from ai.backend.manager.models.role_invitation.row import RoleInvitationRow
from ai.backend.manager.repositories.base import CreatorSpec, IntegrityErrorCheck


@dataclass
class RoleInvitationCreatorSpec(CreatorSpec[RoleInvitationRow]):
    """CreatorSpec for role invitation creation."""

    inviter_user_id: UUID
    invitee_user_id: UUID
    role_id: UUID

    @property
    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return (
            IntegrityErrorCheck(
                violation_type=UniqueConstraintViolationError,
                constraint_name="uq_role_invitations_active",
                error=DuplicateRoleInvitationError(
                    "An active invitation already exists for this user and role"
                ),
            ),
        )

    @override
    def build_row(self) -> RoleInvitationRow:
        return RoleInvitationRow(
            inviter_user_id=self.inviter_user_id,
            invitee_user_id=self.invitee_user_id,
            role_id=self.role_id,
            state=RoleInvitationState.PENDING,
        )
