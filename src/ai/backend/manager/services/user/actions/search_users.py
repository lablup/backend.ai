from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.types import EntityType
from ai.backend.common.data.entity.user import UserEntityType
from ai.backend.manager.actions.v2.ops.base import GlobalSearcherOpsAction
from ai.backend.manager.data.user.types import UserData
from ai.backend.manager.models.user.row import UserRow

__all__ = ("GlobalSearchUsersAction",)


@dataclass(frozen=True)
class GlobalSearchUsersAction(GlobalSearcherOpsAction[UserRow, UserData]):
    """Page through every user in the installation."""

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return UserEntityType()

    @override
    @classmethod
    def action_name(cls) -> str:
        return "global_search_users"
