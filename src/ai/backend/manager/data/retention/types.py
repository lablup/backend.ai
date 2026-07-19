from __future__ import annotations

import enum


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
