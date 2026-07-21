"""Shared retention types — the single source for the retention category enum (BEP-1063)."""

from __future__ import annotations

import enum

__all__ = ("RetentionCategory",)


class RetentionCategory(enum.StrEnum):
    """
    Identifier linking a ``retention_policies`` row to its code-side cleanup
    procedure. A pure identifier carrying no table references.

    The single definition shared across the data, DTO, GraphQL, and API layers.
    """

    LOGS = "logs"
    LOGIN = "login"
    RECONCILE_HISTORY = "reconcile_history"
    ROLES_INVITATIONS = "roles_invitations"
    DEPLOYMENTS = "deployments"
    SESSIONS = "sessions"
    USAGE_RECORDS = "usage_records"
    USAGE_BUCKETS = "usage_buckets"
