"""Listing invitations, from whichever side the reader stands on."""

from __future__ import annotations

from abc import ABC
from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.entity_share import EntityShareEntityType
from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.data.entity.types import EntityIdentifier, EntityType
from ai.backend.common.data.entity.user import UserID
from ai.backend.manager.actions.v2.ops.base import OperationScopeOpsAction, ScopeItem
from ai.backend.manager.data.entity_share.types import EntityShareData
from ai.backend.manager.models.entity_share.row import EntityShareRow
from ai.backend.manager.models.entity_share.scopes import (
    EntityShareRecipientProjectScope,
    EntityShareRecipientScope,
    EntityShareSharerScope,
    EntityShareTargetScope,
)
from ai.backend.manager.models.entity_share.searchers import EntityShareSearcher
from ai.backend.manager.models.scopes import OperationScope

__all__ = (
    "EntityShareRecipientProjectScopeItem",
    "EntityShareRecipientScopeItem",
    "EntityShareSharerScopeItem",
    "EntityShareScopeItem",
    "EntityShareTargetScopeItem",
    "SearchEntitySharesAction",
)


class EntityShareScopeItem(ScopeItem, ABC):
    """One side invitations are read from."""


@dataclass(frozen=True)
class EntityShareRecipientScopeItem(EntityShareScopeItem):
    """The shares addressed to one person, by node or by address."""

    user_id: UserID

    @override
    def scope_id(self) -> EntityIdentifier:
        return self.user_id

    @override
    def operation_scope(self) -> OperationScope:
        return EntityShareRecipientScope(recipient_user_id=self.user_id)


@dataclass(frozen=True)
class EntityShareSharerScopeItem(EntityShareScopeItem):
    """The shares one person sent."""

    user_id: UserID

    @override
    def scope_id(self) -> EntityIdentifier:
        return self.user_id

    @override
    def operation_scope(self) -> OperationScope:
        return EntityShareSharerScope(sharer_user_id=self.user_id)


@dataclass(frozen=True)
class EntityShareRecipientProjectScopeItem(EntityShareScopeItem):
    """The shares addressed to one project."""

    project_id: ProjectID

    @override
    def scope_id(self) -> EntityIdentifier:
        return self.project_id

    @override
    def operation_scope(self) -> OperationScope:
        return EntityShareRecipientProjectScope(project_id=self.project_id)


@dataclass(frozen=True)
class EntityShareTargetScopeItem(EntityShareScopeItem):
    """The shares lending one entity."""

    target: EntityIdentifier

    @override
    def scope_id(self) -> EntityIdentifier:
        return self.target

    @override
    def operation_scope(self) -> OperationScope:
        return EntityShareTargetScope(target=self.target)


@dataclass
class SearchEntitySharesAction(OperationScopeOpsAction[EntityShareRow, EntityShareData]):
    """Page through the invitations the named sides reach, combined with OR.

    Every side is authorized before the read runs, so a caller reaching for one they
    cannot see is refused rather than served the rest.
    """

    items: Sequence[EntityShareScopeItem]
    searcher: EntityShareSearcher

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return EntityShareEntityType()

    @override
    @classmethod
    def action_name(cls) -> str:
        return "search_entity_shares"

    @override
    def scope_targets(self) -> Sequence[EntityIdentifier]:
        return [item.scope_id() for item in self.items]

    @override
    def operation_scopes(self) -> Sequence[OperationScope]:
        return [item.operation_scope() for item in self.items]

    @override
    def to_searcher(self) -> EntityShareSearcher:
        return self.searcher
