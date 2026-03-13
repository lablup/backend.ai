from __future__ import annotations

from collections.abc import Sequence

from ai.backend.common.types import SessionId
from ai.backend.manager.data.session.types import SessionData
from ai.backend.manager.repositories.base import BatchQuerier, NoPagination
from ai.backend.manager.repositories.scheduler.options import SessionConditions
from ai.backend.manager.services.session.actions.search import SearchSessionsAction
from ai.backend.manager.services.session.processors import SessionProcessors


async def load_sessions_by_ids(
    processor: SessionProcessors,
    session_ids: Sequence[SessionId],
) -> list[SessionData | None]:
    if not session_ids:
        return []

    querier = BatchQuerier(
        pagination=NoPagination(),
        conditions=[SessionConditions.by_ids(session_ids)],
    )

    action_result = await processor.search_sessions.wait_for_complete(
        SearchSessionsAction(querier=querier)
    )

    session_map: dict[SessionId, SessionData] = {
        SessionId(data.id): data for data in action_result.data
    }
    return [session_map.get(session_id) for session_id in session_ids]
