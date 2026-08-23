"""Types for role invitation repository operations."""

from __future__ import annotations

from dataclasses import dataclass

from ai.backend.manager.data.role_invitation.types import RoleInvitationData


@dataclass
class RoleInvitationSearchResult:
    """Result from searching role invitations."""

    items: list[RoleInvitationData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool
