"""Scheduling history search operations a query cannot carry.

``message`` is ``sa.Text`` with no index serving a partial match, so the cost rule in
`models/specs/search/AGENTS.md` allows equality and membership only. The partial matches
here shipped before the rule, are marked deprecated in the schema, and are removed in the
next release. Nothing new goes here; the declarations are in `searchable_fields.py`.
"""

from __future__ import annotations

from ai.backend.manager.models.scheduling_history.row import (
    DeploymentHistoryRow,
    KernelSchedulingHistoryRow,
    RouteHistoryRow,
    SessionSchedulingHistoryRow,
)
from ai.backend.manager.models.specs.conditions.string import StringConditions

__all__ = (
    "DeprecatedDeploymentHistoryConditions",
    "DeprecatedKernelSchedulingHistoryConditions",
    "DeprecatedRouteHistoryConditions",
    "DeprecatedSessionSchedulingHistoryConditions",
)


class DeprecatedSessionSchedulingHistoryConditions:
    """Partial matches on the session history row's message."""

    message = StringConditions(SessionSchedulingHistoryRow.message)


class DeprecatedKernelSchedulingHistoryConditions:
    """Partial matches on the kernel history row's message."""

    message = StringConditions(KernelSchedulingHistoryRow.message)


class DeprecatedDeploymentHistoryConditions:
    """Partial matches on the deployment history row's message."""

    message = StringConditions(DeploymentHistoryRow.message)


class DeprecatedRouteHistoryConditions:
    """Partial matches on the route history row's message."""

    message = StringConditions(RouteHistoryRow.message)
