from __future__ import annotations

import uuid
from collections.abc import Sequence

from ai.backend.manager.api.gql.base import UUIDInMatchSpec
from ai.backend.manager.data.user.types import UserData
from ai.backend.manager.repositories.base import BatchQuerier, NoPagination
from ai.backend.manager.repositories.user.options import UserConditions
from ai.backend.manager.services.user.actions.search_users import SearchUsersAction
from ai.backend.manager.services.user.processors import UserProcessors


async def load_users_by_ids(
    processor: UserProcessors,
    user_ids: Sequence[uuid.UUID],
) -> list[UserData | None]:
    """Batch load users by their UUIDs.

    Args:
        processor: The user processor.
        user_ids: Sequence of user UUIDs to load.

    Returns:
        List of UserData (or None if not found) in the same order as user_ids.
    """
    if not user_ids:
        return []

    querier = BatchQuerier(
        pagination=NoPagination(),
        conditions=[
            UserConditions.by_uuid_in(UUIDInMatchSpec(values=list(user_ids), negated=False))
        ],
    )

    action_result = await processor.search_users.wait_for_complete(
        SearchUsersAction(querier=querier)
    )

    user_map = {user.uuid: user for user in action_result.users}
    return [user_map.get(user_id) for user_id in user_ids]
