from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.common.data.entity.user import UserID
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.actions.v2.single_entity.base import BaseSingleEntityAction
from ai.backend.manager.data.dotfile.types import DotfileData
from ai.backend.manager.models.dotfile.queriers import DotfileQuerier


@dataclass(frozen=True)
class GetDotfileAction(BaseSingleEntityAction):
    user_id: UserID
    querier: DotfileQuerier

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
        return "get_dotfile"


@dataclass(frozen=True)
class GetDotfileActionResult:
    dotfile: DotfileData
