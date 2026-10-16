from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.common.data.entity.user import UserID
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.actions.v2.single_entity.base import BaseSingleEntityAction
from ai.backend.manager.data.dotfile.types import DotfileData
from ai.backend.manager.models.dotfile.searchers import DotfileSearcher


@dataclass(frozen=True)
class GetUserDotfilesAction(BaseSingleEntityAction):
    """The user's dotfiles the searcher selects; the user bounds the search, not the searcher."""

    user_id: UserID
    searcher: DotfileSearcher

    @override
    def entity_id(self) -> EntityIdentifier:
        return self.user_id

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET

    @override
    @classmethod
    def action_name(cls) -> str:
        return "get_user_dotfiles"


@dataclass(frozen=True)
class GetUserDotfilesActionResult:
    dotfiles: list[DotfileData]
