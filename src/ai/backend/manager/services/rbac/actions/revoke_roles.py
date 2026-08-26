"""Taking roles of an organization back from a member."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.role import RoleID
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.services.rbac.actions.base import (
    BaseOrganizationMemberAction,
    OrganizationMemberActionResult,
)

__all__ = (
    "RevokeRolesAction",
    "RevokeRolesActionResult",
)


@dataclass(frozen=True)
class RevokeRolesAction(BaseOrganizationMemberAction):
    """Carries no spec, for the same reason :class:`GrantRolesAction` does not."""

    role_ids: Sequence[RoleID]

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "revoke_roles"


@dataclass(frozen=True)
class RevokeRolesActionResult(OrganizationMemberActionResult):
    pass
