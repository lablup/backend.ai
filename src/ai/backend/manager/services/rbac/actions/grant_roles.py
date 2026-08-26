"""Giving a member roles of the organization they are in."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.role import RoleID
from ai.backend.common.data.entity.user import UserID
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.services.rbac.actions.base import (
    BaseOrganizationMemberAction,
    OrganizationMemberActionResult,
)

__all__ = (
    "GrantRolesAction",
    "GrantRolesActionResult",
)


@dataclass(frozen=True)
class GrantRolesAction(BaseOrganizationMemberAction):
    """Carries no spec: what it writes is the role a user holds, one table whichever
    organization the roles belong to."""

    role_ids: Sequence[RoleID]
    granted_by: UserID

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "grant_roles"


@dataclass(frozen=True)
class GrantRolesActionResult(OrganizationMemberActionResult):
    pass
