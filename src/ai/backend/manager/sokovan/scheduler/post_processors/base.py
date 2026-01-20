"""Base class for post-processors."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from ai.backend.manager.data.kernel.types import KernelStatus
from ai.backend.manager.data.session.types import SessionStatus

if TYPE_CHECKING:
    from ai.backend.manager.sokovan.scheduler.results import (
        KernelExecutionResult,
        SessionExecutionResult,
    )


# =============================================================================
# Session Post-Processor Types
# =============================================================================


@dataclass
class PostProcessorContext:
    """Context passed to session post-processors."""

    result: SessionExecutionResult
    target_statuses: set[SessionStatus] = field(default_factory=set)


class PostProcessor(ABC):
    """Abstract base class for session post-processors.

    Post-processors execute common logic after handler execution.
    They receive the execution result and target status, and perform
    side effects like marking schedules or invalidating caches.
    """

    @abstractmethod
    async def execute(self, context: PostProcessorContext) -> None:
        """Execute the post-processing logic.

        Args:
            context: Post-processor context containing result and target status
        """
        raise NotImplementedError


# =============================================================================
# Kernel Post-Processor Types
# =============================================================================


@dataclass
class KernelPostProcessorContext:
    """Context passed to kernel post-processors."""

    result: KernelExecutionResult
    target_statuses: set[KernelStatus] = field(default_factory=set)


class KernelPostProcessor(ABC):
    """Abstract base class for kernel post-processors.

    Kernel post-processors execute common logic after kernel handler execution.
    They receive the kernel execution result and perform side effects like
    marking schedules for session termination checks.
    """

    @abstractmethod
    async def execute(self, context: KernelPostProcessorContext) -> None:
        """Execute the kernel post-processing logic.

        Args:
            context: Kernel post-processor context containing result
        """
        raise NotImplementedError
