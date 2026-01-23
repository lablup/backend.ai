from __future__ import annotations

import uuid
from collections.abc import Sequence
from typing import Optional

from ai.backend.manager.data.error_log.types import ErrorLogData
from ai.backend.manager.repositories.base import BatchQuerier, OffsetPagination
from ai.backend.manager.repositories.error_log import ErrorLogConditions
from ai.backend.manager.services.error_log.actions.search import SearchErrorLogsAction
from ai.backend.manager.services.error_log.processors import ErrorLogProcessors


async def load_error_logs_by_ids(
    processor: ErrorLogProcessors,
    error_log_ids: Sequence[uuid.UUID],
) -> list[Optional[ErrorLogData]]:
    """Batch load error logs by their IDs.

    Args:
        processor: The error log processor.
        error_log_ids: Sequence of error log UUIDs to load.

    Returns:
        List of ErrorLogData (or None if not found) in the same order as error_log_ids.
    """
    if not error_log_ids:
        return []

    querier = BatchQuerier(
        pagination=OffsetPagination(limit=len(error_log_ids)),
        conditions=[ErrorLogConditions.by_ids(error_log_ids)],
    )

    action_result = await processor.search.wait_for_complete(SearchErrorLogsAction(querier=querier))

    error_log_map = {error_log.id: error_log for error_log in action_result.data}
    return [error_log_map.get(error_log_id) for error_log_id in error_log_ids]
