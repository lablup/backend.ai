"""User search over the scopes users are reachable from."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.types import EntityType
from ai.backend.common.data.entity.user import UserEntityType
from ai.backend.manager.actions.v2.ops.base import ScopedSearchOpsAction
from ai.backend.manager.data.user.types import UserData
from ai.backend.manager.models.user.row import UserRow

__all__ = ("ScopedSearchUsersAction",)


@dataclass(frozen=True)
class ScopedSearchUsersAction(ScopedSearchOpsAction[UserRow, UserData]):
    """Page through the users the named scopes reach, combined with OR.

    Every scope is authorized before the read runs, so a caller reaching for one they
    cannot see is refused rather than served the rest.
    """

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return UserEntityType()

    @override
    @classmethod
    def action_name(cls) -> str:
        return "scoped_search_users"
