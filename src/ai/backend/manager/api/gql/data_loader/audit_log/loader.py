from __future__ import annotations

import uuid
from collections.abc import Sequence
from typing import Optional

from ai.backend.manager.data.audit_log.types import AuditLogData
from ai.backend.manager.repositories.audit_log import AuditLogConditions
from ai.backend.manager.repositories.base import BatchQuerier, OffsetPagination
from ai.backend.manager.services.audit_log.actions.search import SearchAuditLogsAction
from ai.backend.manager.services.audit_log.processors import AuditLogProcessors


async def load_audit_logs_by_ids(
    processor: AuditLogProcessors,
    audit_log_ids: Sequence[uuid.UUID],
) -> list[Optional[AuditLogData]]:
    """Batch load audit logs by their IDs.

    Args:
        processor: The audit log processor.
        audit_log_ids: Sequence of audit log UUIDs to load.

    Returns:
        List of AuditLogData (or None if not found) in the same order as audit_log_ids.
    """
    if not audit_log_ids:
        return []

    querier = BatchQuerier(
        pagination=OffsetPagination(limit=len(audit_log_ids)),
        conditions=[AuditLogConditions.by_ids(audit_log_ids)],
    )

    action_result = await processor.search.wait_for_complete(SearchAuditLogsAction(querier=querier))

    audit_log_map = {audit_log.id: audit_log for audit_log in action_result.data}
    return [audit_log_map.get(audit_log_id) for audit_log_id in audit_log_ids]
