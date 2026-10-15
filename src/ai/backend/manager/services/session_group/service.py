from __future__ import annotations

from ai.backend.common.data.entity.session_group import SessionGroupEntityType
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.actions.v2.bulk.result import PartialBulkEntityResult, PartialBulkResult
from ai.backend.manager.actions.v2.ops.result import EntityOpsResult
from ai.backend.manager.data.session_group.types import SessionGroupData
from ai.backend.manager.errors.base.entity import EntityNotFoundError
from ai.backend.manager.repositories.ops.repository import OpsRepository
from ai.backend.manager.services.session_group.actions.bulk_get import BulkGetSessionGroupsAction
from ai.backend.manager.services.session_group.actions.get import GetSessionGroupAction

__all__ = ("SessionGroupService",)


class SessionGroupService:
    """The reads by id, which leave out a deployment's group; the searches run against ops."""

    _repository: OpsRepository[SessionGroupData]

    def __init__(self, repository: OpsRepository[SessionGroupData]) -> None:
        self._repository = repository

    async def get(self, action: GetSessionGroupAction) -> EntityOpsResult[SessionGroupData]:
        """Read one session group by its id; a deployment's group is not found."""
        found = (await self._repository.search_in_global(action.to_searcher())).items
        if not found:
            raise EntityNotFoundError(
                f"Session group {action.group_id} not found",
                entity_type=SessionGroupEntityType(),
                operation=ActionOperationType.GET,
            )
        return EntityOpsResult(data=found[0])

    async def bulk_get_ids(
        self, action: BulkGetSessionGroupsAction
    ) -> PartialBulkResult[SessionGroupData]:
        """Read each named session group, answering empty for one that is not there."""
        result = await self._repository.search_in_global(action.to_searcher())
        found = {data.id: data for data in result.items}
        return PartialBulkResult(
            items=[
                PartialBulkEntityResult[SessionGroupData].succeeded(group_id, found[group_id])
                if group_id in found
                else PartialBulkEntityResult[SessionGroupData].nothing(group_id)
                for group_id in action.ids
            ]
        )
