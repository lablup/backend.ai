"""
Common types for event_stream DTO v2.

Re-exports domain-level enums from the v1 streaming types module.
"""

from __future__ import annotations

from ai.backend.common.dto.manager.streaming.types import (
    BgtaskSSEEventName,
    SessionEventScope,
)

__all__ = (
    "BgtaskSSEEventName",
    "SessionEventScope",
)
