"""
Common types for operations system.
"""

from __future__ import annotations

from enum import StrEnum

__all__ = (
    "ErrorLogSeverity",
    "ManagerStatus",
    "SchedulerOps",
)


class ErrorLogSeverity(StrEnum):
    """Severity levels for error log entries."""

    CRITICAL = "critical"
    ERROR = "error"
    WARNING = "warning"


class ManagerStatus(StrEnum):
    """Manager operational statuses."""

    TERMINATED = "terminated"
    PREPARING = "preparing"
    RUNNING = "running"
    FROZEN = "frozen"


class SchedulerOps(StrEnum):
    """Scheduler operations that can be performed via the manager API."""

    INCLUDE_AGENTS = "include-agents"
    EXCLUDE_AGENTS = "exclude-agents"
