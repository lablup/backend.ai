"""Post-processor for invalidating kernel-related cache."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from ai.backend.common.types import AccessKey
from ai.backend.logging import BraceStyleAdapter

from .base import PostProcessor, PostProcessorContext

if TYPE_CHECKING:
    from ai.backend.manager.repositories.scheduler.repository import SchedulerRepository

log = BraceStyleAdapter(logging.getLogger(__name__))


class CacheInvalidationPostProcessor(PostProcessor):
    """Post-processor that invalidates kernel-related cache for affected access keys."""

    def __init__(self, repository: SchedulerRepository) -> None:
        self._repository = repository

    async def execute(self, context: PostProcessorContext) -> None:
        """Invalidate cache for all affected access keys."""
        affected_keys: set[AccessKey] = set()

        for info in context.result.successes:
            if info.access_key:
                affected_keys.add(info.access_key)
        for info in context.result.failures:
            if info.access_key:
                affected_keys.add(info.access_key)

        if affected_keys:
            await self._repository.invalidate_kernel_related_cache(list(affected_keys))
            log.debug(
                "Invalidated kernel-related cache for {} access keys",
                len(affected_keys),
            )
