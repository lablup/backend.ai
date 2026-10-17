from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override

from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.common.data.entity.user import UserID
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.dotfile.conditions import DotfileConditions
from ai.backend.manager.models.scopes import ExistenceCheck, ScopeTarget


@dataclass(frozen=True)
class UserDotfileTarget(ScopeTarget):
    """The dotfiles one user owns."""

    user_id: UserID

    @override
    def scope_id(self) -> EntityIdentifier:
        return self.user_id

    @override
    def to_condition(self) -> QueryCondition:
        return DotfileConditions.by_entity(self.user_id)

    @property
    @override
    def existence_checks(self) -> Sequence[ExistenceCheck[Any]]:
        # The action's user check or the caller's user lock already answered for it.
        return ()
