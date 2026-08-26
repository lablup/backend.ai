"""Putting a user in an organization, with the roles that come with it."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.role import RoleID
from ai.backend.common.data.entity.user import UserID
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.models.base import Base
from ai.backend.manager.models.specs.relation import RelationCreator
from ai.backend.manager.services.rbac.actions.base import (
    BaseOrganizationMemberAction,
    OrganizationMemberActionResult,
)

__all__ = (
    "EnrollAction",
    "EnrollActionResult",
)


@dataclass(frozen=True)
class EnrollAction[TRow: Base](BaseOrganizationMemberAction):
    """``role_ids`` names what to give; ``None`` gives the organization's auto-assign
    roles. A named role the organization does not hold is refused."""

    creator: RelationCreator[TRow]
    granted_by: UserID
    role_ids: Sequence[RoleID] | None = None

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.CREATE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "enroll_organization_member"


@dataclass(frozen=True)
class EnrollActionResult(OrganizationMemberActionResult):
    """``enrolled`` is false when the user was already a member; the roles are granted
    either way."""

    enrolled: bool
