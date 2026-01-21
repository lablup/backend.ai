"""Generic recorder module for sokovan coordinators.

This module provides base recorder functionality that can be specialized
for different coordinator contexts (scheduler, deployment, route).
"""

from .context import RecorderContext
from .exceptions import (
    NestedPhaseError,
    RecorderError,
    StepWithoutPhaseError,
)
from .pool import RecordPool
from .recorder import TransitionRecorder
from .types import (
    EntityIdT,
    ExecutionRecord,
    PhaseRecord,
    StepRecord,
    StepStatus,
)

__all__ = [
    "EntityIdT",
    "ExecutionRecord",
    "NestedPhaseError",
    "PhaseRecord",
    "RecordPool",
    "RecorderContext",
    "RecorderError",
    "StepRecord",
    "StepStatus",
    "StepWithoutPhaseError",
    "TransitionRecorder",
]
