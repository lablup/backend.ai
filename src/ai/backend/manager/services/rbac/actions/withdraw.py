"""Taking a user out of an organization, and its roles with them."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.models.base import Base
from ai.backend.manager.models.specs.relation import RelationPurger
from ai.backend.manager.services.rbac.actions.base import (
    BaseOrganizationMemberAction,
    OrganizationMemberActionResult,
)

__all__ = (
    "WithdrawAction",
    "WithdrawActionResult",
)


@dataclass(frozen=True)
class WithdrawAction[TRow: Base](BaseOrganizationMemberAction):
    purger: RelationPurger[TRow]

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.PURGE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "withdraw_organization_member"


@dataclass(frozen=True)
class WithdrawActionResult(OrganizationMemberActionResult):
    """``withdrawn`` is false when the user was not a member; the roles are taken back
    either way."""

    withdrawn: bool
