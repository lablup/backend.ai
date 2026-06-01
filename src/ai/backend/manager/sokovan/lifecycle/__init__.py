"""Generic, entity-agnostic lifecycle coordination primitives."""

from ai.backend.manager.sokovan.lifecycle.base import (
    LifecycleEntitySource,
    LifecycleHandler,
    LifecycleNeededFlags,
    LifecycleResult,
    LifecycleStage,
    LifecycleStageRunner,
    LifecycleTaskSpec,
    LifecycleTransitionApplier,
)
from ai.backend.manager.sokovan.lifecycle.coordinator import LifecycleCoordinator

__all__ = [
    "LifecycleCoordinator",
    "LifecycleEntitySource",
    "LifecycleHandler",
    "LifecycleNeededFlags",
    "LifecycleResult",
    "LifecycleStage",
    "LifecycleStageRunner",
    "LifecycleTaskSpec",
    "LifecycleTransitionApplier",
]
