"""Factory functions for creating post-processors."""

from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING

from .base import KernelPostProcessor, PostProcessor
from .cache_invalidation import CacheInvalidationPostProcessor
from .kernel_schedule_marking import KernelScheduleMarkingPostProcessor
from .schedule_marking import ScheduleMarkingPostProcessor

if TYPE_CHECKING:
    from ai.backend.manager.repositories.scheduler.repository import SchedulerRepository
    from ai.backend.manager.sokovan.scheduling_controller import SchedulingController


def create_session_post_processors(
    scheduling_controller: SchedulingController,
    repository: SchedulerRepository,
) -> Sequence[PostProcessor]:
    """Create the default sequence of post-processors for session handlers.

    Args:
        scheduling_controller: Controller for marking schedules
        repository: Repository for cache invalidation

    Returns:
        Sequence of post-processors to execute in order
    """
    return [
        ScheduleMarkingPostProcessor(scheduling_controller),
        CacheInvalidationPostProcessor(repository),
    ]


def create_kernel_post_processors(
    scheduling_controller: SchedulingController,
) -> Sequence[KernelPostProcessor]:
    """Create the default sequence of post-processors for kernel handlers.

    Args:
        scheduling_controller: Controller for marking schedules

    Returns:
        Sequence of kernel post-processors to execute in order
    """
    return [
        KernelScheduleMarkingPostProcessor(scheduling_controller),
    ]
