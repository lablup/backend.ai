"""The operations that build the permission graph.

Each write is one ops primitive, so nothing here opens a transaction: what has to land
together — a roster place and the role it grants — lands in the primitive it is
composed of.
"""

from __future__ import annotations

from typing import Any

from ai.backend.manager.repositories.rbac.relation_repository import RbacRelationRepository
from ai.backend.manager.repositories.rbac.roster_repository import RbacRosterRepository
from ai.backend.manager.services.rbac.actions.relation.base import (
    RelationLinkResult,
    RelationSwitchResult,
    RelationUnlinkResult,
)
from ai.backend.manager.services.rbac.actions.relation.create import (
    CreateRelationAction,
    CreateRelationActionResult,
)
from ai.backend.manager.services.rbac.actions.relation.purge import (
    PurgeRelationAction,
    PurgeRelationActionResult,
)
from ai.backend.manager.services.rbac.actions.relation.switch import (
    DeleteRelationAction,
    DeleteRelationActionResult,
    RestoreRelationAction,
    RestoreRelationActionResult,
)
from ai.backend.manager.services.rbac.actions.roster.join_project import (
    JoinProjectAction,
    JoinProjectActionResult,
)
from ai.backend.manager.services.rbac.actions.roster.leave_project import (
    LeaveProjectAction,
    LeaveProjectActionResult,
)

__all__ = ("RbacRelationService", "RbacRosterService")


class RbacRelationService:
    """Linking two entities and unlinking them.

    One method per direction: which relation a run is about travels on the action's
    spec, so every kind goes through the same two.
    """

    _repository: RbacRelationRepository

    def __init__(self, repository: RbacRelationRepository) -> None:
        self._repository = repository

    async def create(
        self, action: CreateRelationAction[Any, Any, Any]
    ) -> CreateRelationActionResult[Any, Any]:
        written = await self._repository.create(
            [(pair.scope, pair.target) for pair in action.pairs], action.creator
        )
        return CreateRelationActionResult(
            results=[
                RelationLinkResult(pair=pair, linked=linked)
                for pair, linked in zip(action.pairs, written, strict=True)
            ]
        )

    async def purge(
        self, action: PurgeRelationAction[Any, Any, Any]
    ) -> PurgeRelationActionResult[Any, Any]:
        unlinked = await self._repository.purge(
            [(pair.scope, pair.target) for pair in action.pairs], action.purger
        )
        return PurgeRelationActionResult(
            results=[
                RelationUnlinkResult(pair=pair, unlinked=was_linked)
                for pair, was_linked in zip(action.pairs, unlinked, strict=True)
            ]
        )

    async def delete(
        self, action: DeleteRelationAction[Any, Any, Any]
    ) -> DeleteRelationActionResult[Any, Any]:
        switched = await self._repository.delete(
            [(pair.scope, pair.target) for pair in action.pairs], action.updater
        )
        return DeleteRelationActionResult(
            results=[
                RelationSwitchResult(pair=pair, switched=moved)
                for pair, moved in zip(action.pairs, switched, strict=True)
            ]
        )

    async def restore(
        self, action: RestoreRelationAction[Any, Any, Any]
    ) -> RestoreRelationActionResult[Any, Any]:
        switched = await self._repository.restore(
            [(pair.scope, pair.target) for pair in action.pairs], action.updater
        )
        return RestoreRelationActionResult(
            results=[
                RelationSwitchResult(pair=pair, switched=moved)
                for pair, moved in zip(action.pairs, switched, strict=True)
            ]
        )


class RbacRosterService:
    """Putting a user on a project's roster and taking them off."""

    _repository: RbacRosterRepository

    def __init__(self, repository: RbacRosterRepository) -> None:
        self._repository = repository

    async def join(self, action: JoinProjectAction) -> JoinProjectActionResult:
        members = await self._repository.join_members(
            action.project_id, action.user_ids, action.role_id
        )
        return JoinProjectActionResult(members=members)

    async def leave(self, action: LeaveProjectAction) -> LeaveProjectActionResult:
        result = await self._repository.leave_members(action.project_id, action.user_ids)
        return LeaveProjectActionResult(members=result.members, failures=result.failures)
