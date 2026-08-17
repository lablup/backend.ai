from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta

from ai.backend.common.data.entity.action import ActionID
from ai.backend.manager.actions.v2.lookup.bulk_base import BulkLookupKeyResult

__all__ = ("BulkLookupActionResultMeta", "BulkLookupActionProcessResult")


@dataclass
class BulkLookupActionResultMeta:
    """Outcome metadata for a bulk lookup run, resolved for each key separately.

    The run has no status of its own: every key carries one, and each audit row covers
    a single key.
    """

    action_id: ActionID
    key_results: Sequence[BulkLookupKeyResult]
    started_at: datetime
    ended_at: datetime
    duration: timedelta


@dataclass
class BulkLookupActionProcessResult:
    meta: BulkLookupActionResultMeta
