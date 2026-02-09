from __future__ import annotations

import uuid
from collections.abc import Sequence

from ai.backend.manager.api.gql.base import UUIDInMatchSpec
from ai.backend.manager.data.group.types import GroupData
from ai.backend.manager.repositories.base import BatchQuerier, NoPagination
from ai.backend.manager.repositories.group.options import GroupConditions
from ai.backend.manager.services.group.actions.search_projects import SearchProjectsAction
from ai.backend.manager.services.group.processors import GroupProcessors


async def load_projects_by_ids(
    processor: GroupProcessors,
    project_ids: Sequence[uuid.UUID],
) -> list[GroupData | None]:
    """Batch load projects by their IDs.

    Args:
        processor: The group processor.
        project_ids: Sequence of project UUIDs to load.

    Returns:
        List of GroupData (or None if not found) in the same order as project_ids.
    """
    if not project_ids:
        return []

    querier = BatchQuerier(
        pagination=NoPagination(),
        conditions=[
            GroupConditions.by_id_in(UUIDInMatchSpec(values=list(project_ids), negated=False))
        ],
    )

    action_result = await processor.search_projects.wait_for_complete(
        SearchProjectsAction(querier=querier)
    )

    project_map = {group.id: group for group in action_result.items}
    return [project_map.get(project_id) for project_id in project_ids]
