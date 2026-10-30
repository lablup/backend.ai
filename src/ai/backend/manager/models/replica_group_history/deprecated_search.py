"""Replica-group history search operations a query cannot carry.

``message`` is ``sa.Text`` with no index serving a partial match, so the cost rule in
`models/specs/search/AGENTS.md` allows equality and membership only. The partial matches
here shipped before the rule, are marked deprecated in the schema, and are removed in the
next release. Nothing new goes here; the declarations are in `searchable_fields.py`.
"""

from __future__ import annotations

from ai.backend.manager.models.replica_group_history.row import ReplicaGroupHistoryRow
from ai.backend.manager.models.specs.conditions.string import StringConditions

__all__ = ("DeprecatedReplicaGroupHistoryConditions",)


class DeprecatedReplicaGroupHistoryConditions:
    """Partial matches on the history row's message."""

    message = StringConditions(ReplicaGroupHistoryRow.message)
