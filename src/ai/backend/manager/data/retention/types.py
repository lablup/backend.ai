from __future__ import annotations

import enum
from dataclasses import dataclass


class RetentionCategory(enum.StrEnum):
    """
    Identifier linking a ``retention_policies`` row to its code-side cleanup
    procedure. A pure identifier carrying no table references.
    """

    LOGS = "logs"
    LOGIN = "login"
    RECONCILE_HISTORY = "reconcile_history"
    ROLES_INVITATIONS = "roles_invitations"
    DEPLOYMENTS = "deployments"
    SESSIONS = "sessions"
    USAGE_RECORDS = "usage_records"
    USAGE_BUCKETS = "usage_buckets"


@dataclass(frozen=True)
class RetentionPurgeResult:
    """Outcome of purging one category's older-than-threshold rows.

    ``deleted_count`` is the total rows removed across the category's tables,
    letting the sweep account the result against its per-tick budget.
    """

    category: RetentionCategory
    deleted_count: int
