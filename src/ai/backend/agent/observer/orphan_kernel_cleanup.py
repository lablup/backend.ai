from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Optional, override

from ai.backend.common.clients.valkey_client.valkey_schedule import ValkeyScheduleClient
from ai.backend.common.clients.valkey_client.valkey_schedule.client import (
    ORPHAN_KERNEL_THRESHOLD_SEC,
)
from ai.backend.common.events.event_types.kernel.types import KernelLifecycleEventReason
from ai.backend.common.observer.types import AbstractObserver
from ai.backend.common.types import KernelId, SessionId
from ai.backend.logging.utils import BraceStyleAdapter

from ..types import LifecycleEvent

if TYPE_CHECKING:
    from ..agent import AbstractAgent

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class OrphanKernelCleanupObserver(AbstractObserver):
    """
    Observer that periodically detects and cleans up orphan kernels.

    Orphan kernels are containers that exist in Agent but have been
    terminated from Manager's DB. Detection is based on comparing
    kernel.last_check with agent_last_check timestamps.

    Cleanup condition (strict):
        (agent_last_check exists) AND
        (kernel status exists in Redis) AND
        (kernel.last_check < agent_last_check - THRESHOLD)

    All other cases (no Redis entry, no agent_last_check, etc.) are skipped.
    """

    def __init__(
        self,
        agent: AbstractAgent,
        valkey_schedule_client: ValkeyScheduleClient,
    ) -> None:
        self._agent = agent
        self._valkey_schedule_client = valkey_schedule_client

    @property
    @override
    def name(self) -> str:
        return "orphan_kernel_cleanup"

    @override
    async def observe(self) -> None:
        # 1. Get agent's last_check timestamp
        agent_last_check = await self._valkey_schedule_client.get_agent_last_check(self._agent.id)
        if agent_last_check is None:
            # Manager hasn't checked this agent yet - do nothing
            log.debug(
                "No agent_last_check found for agent {}, skipping orphan cleanup", self._agent.id
            )
            return

        # 2. Get kernels from registry
        kernel_registry = self._agent.kernel_registry
        if not kernel_registry:
            return

        # 3. Get kernel presence statuses (read-only)
        kernel_ids = list(kernel_registry.keys())
        statuses = await self._valkey_schedule_client.get_kernel_presence_batch(kernel_ids)

        # 4. Find orphan kernels
        orphan_kernels: list[tuple[KernelId, SessionId]] = []
        for kernel_id, kernel in kernel_registry.items():
            status = statuses.get(kernel_id)
            if status is None:
                # No Redis entry - skip (not enough info to decide)
                continue

            # Skip if last_check is None (not enough info to decide)
            if status.last_check is None:
                log.debug(
                    "Kernel {} has no last_check timestamp, skipping orphan check",
                    kernel_id,
                )
                continue

            # Strict condition: kernel.last_check < agent_last_check - THRESHOLD
            if status.last_check < agent_last_check - ORPHAN_KERNEL_THRESHOLD_SEC:
                orphan_kernels.append((kernel_id, kernel.session_id))
                log.info(
                    "Detected orphan kernel: {} (last_check={}, agent_last_check={}, threshold={})",
                    kernel_id,
                    status.last_check,
                    agent_last_check,
                    ORPHAN_KERNEL_THRESHOLD_SEC,
                )

        # 5. Cleanup orphan kernels via lifecycle event
        for kernel_id, session_id in orphan_kernels:
            try:
                log.warning("Cleaning up orphan kernel: {}", kernel_id)
                await self._agent.inject_container_lifecycle_event(
                    kernel_id,
                    session_id,
                    LifecycleEvent.DESTROY,
                    KernelLifecycleEventReason.NOT_FOUND_IN_MANAGER,
                    suppress_events=True,
                )
            except Exception:
                log.exception("Failed to cleanup orphan kernel {}", kernel_id)

    @override
    def observe_interval(self) -> float:
        return 300.0  # 5 minutes

    @classmethod
    @override
    def timeout(cls) -> Optional[float]:
        return 30.0  # 30 seconds

    @override
    async def cleanup(self) -> None:
        pass
