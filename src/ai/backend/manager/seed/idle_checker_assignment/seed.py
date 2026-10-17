from __future__ import annotations

import uuid
from collections.abc import Sequence
from typing import Literal, assert_never, override

from ai.backend.common.data.entity.domain import DomainID
from ai.backend.common.data.entity.idle_checker import IdleCheckerID
from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.data.entity.resource_group import ResourceGroupID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.common.data.entity.user import UserID
from ai.backend.manager.models.idle_checker.creators import IdleCheckerAssignmentCreator
from ai.backend.manager.repositories.ops.v2.seed.types import SeedRelationWrite
from ai.backend.manager.seed.base import SeedItems, SeedRejection, SeedRelationItem


class IdleCheckerAssignmentSeed(SeedRelationItem):
    """One idle checker applied to a scope, linked as the assignment API links one.
    ``enabled`` is the value a new row starts with; a row already there keeps its own."""

    idle_checker_id: IdleCheckerID
    scope_type: Literal["domain", "project", "resource_group", "user"]
    scope_id: uuid.UUID
    enabled: bool = True

    @override
    def key(self) -> str:
        return f"{self.scope_type}:{self.scope_id}:{self.idle_checker_id}"

    @override
    def write(self) -> SeedRelationWrite:
        return SeedRelationWrite(
            creator=IdleCheckerAssignmentCreator(enabled=self.enabled),
            scope=self._scope(),
            target=self.idle_checker_id,
        )

    def _scope(self) -> EntityIdentifier:
        match self.scope_type:
            case "domain":
                return DomainID(self.scope_id)
            case "project":
                return ProjectID(self.scope_id)
            case "resource_group":
                return ResourceGroupID(self.scope_id)
            case "user":
                return UserID(self.scope_id)
            case _:
                assert_never(self.scope_type)

    @override
    def check(self) -> list[str]:
        return []

    @override
    @classmethod
    def reject(cls, files: Sequence[SeedItems[IdleCheckerAssignmentSeed]]) -> list[SeedRejection]:
        """None: the creator refuses an item naming a missing scope or checker when it is
        written."""
        return []
