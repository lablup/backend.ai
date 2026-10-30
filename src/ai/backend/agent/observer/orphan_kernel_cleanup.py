from __future__ import annotations

import logging
import time
from typing import TYPE_CHECKING, Any, override

from ai.backend.agent.types import LifecycleEvent
from ai.backend.common.clients.valkey_client.valkey_schedule import ValkeyScheduleClient
from ai.backend.common.clients.valkey_client.valkey_schedule.client import (
    ORPHAN_KERNEL_THRESHOLD_SEC,
    HealthCheckStatus,
    KernelStatus,
)
from ai.backend.common.events.event_types.kernel.types import KernelLifecycleEventReason
from ai.backend.common.observer.types import AbstractObserver
from ai.backend.common.types import KernelId, SessionId
from ai.backend.logging.structured import StructuredLogger

if TYPE_CHECKING:
    from ai.backend.agent.agent import AbstractAgent

log = StructuredLogger(logging.getLogger(__spec__.name))


class OrphanKernelCleanupObserver(AbstractObserver):
    """
    Reaps kernels the manager no longer tracks: (a) checked once, then stopped
    (``last_check < agent_last_check - THRESHOLD``); (b) running here but never checked for
    THRESHOLD while the manager's sweep mark is fresh. Without a fresh mark, only (a) runs.
    """

    _agent: AbstractAgent[Any, Any]
    _valkey_schedule_client: ValkeyScheduleClient
    # kernel_id -> monotonic time first seen running and unchecked; rule (b)'s debounce.
    _unknown_since: dict[KernelId, float]

    def __init__(
        self,
        agent: AbstractAgent[Any, Any],
        valkey_schedule_client: ValkeyScheduleClient,
    ) -> None:
        self._agent = agent
        self._valkey_schedule_client = valkey_schedule_client
        self._unknown_since = {}

    @property
    @override
    def name(self) -> str:
        return "orphan_kernel_cleanup"

    @override
    async def observe(self) -> None:
        # 1. Get agent's last_check timestamp. Only rule (a) needs it.
        agent_last_check = await self._valkey_schedule_client.get_agent_last_check(self._agent.id)

        # 2. Rule (b) runs only while the manager's cluster-wide sweep mark is fresh.
        sweep_epoch = await self._valkey_schedule_client.get_manager_sweep_epoch()
        reap_unknown = False
        if sweep_epoch is None:
            log.debug("orphan kernel rule (b) skipped, no manager sweep mark")
        else:
            now = await self._valkey_schedule_client.get_redis_time()
            if now - sweep_epoch > ORPHAN_KERNEL_THRESHOLD_SEC:
                log.debug(
                    "orphan kernel rule (b) skipped, manager sweep is stale",
                    sweep_age_sec=now - sweep_epoch,
                )
            else:
                reap_unknown = True
        if not reap_unknown:
            # Rule (b)'s debounce must restart once the mark is fresh again.
            self._unknown_since.clear()

        if agent_last_check is None and not reap_unknown:
            log.debug("orphan kernel cleanup skipped, no agent last check", agent_id=self._agent.id)
            return

        # 3. Get kernels from registry
        kernel_registry = self._agent.kernel_registry
        if not kernel_registry:
            self._unknown_since.clear()
            return

        # 4. Get kernel presence statuses (read-only)
        kernel_ids = list(kernel_registry.keys())
        statuses = await self._valkey_schedule_client.get_kernel_presence_batch(kernel_ids)

        # 5. Find orphan kernels
        # (kernel_id, session_id, suppress_events)
        orphan_kernels: list[tuple[KernelId, SessionId, bool]] = []
        unknown: dict[KernelId, float] = {}
        since_now = time.monotonic()
        for kernel_id, kernel in kernel_registry.items():
            status = statuses.get(kernel_id)
            if status is None:
                continue
            if status.last_check is not None:
                if self._was_dropped_by_manager(status, agent_last_check):
                    orphan_kernels.append((kernel_id, kernel.session_id, True))
                    log.debug(
                        "orphan kernel detected",
                        kernel_id=kernel_id,
                        last_check=status.last_check,
                        agent_last_check=agent_last_check,
                        threshold_sec=ORPHAN_KERNEL_THRESHOLD_SEC,
                    )
                continue
            # (b) Only a running container: the manager stamps kernels it holds RUNNING, so one
            # whose DB row stays non-RUNNING (e.g. CREATING after a lost KernelStarted) for
            # THRESHOLD is reaped too.
            if not reap_unknown or status.presence != HealthCheckStatus.HEALTHY:
                continue
            # Still initializing: the init timeout, not this rule, decides its fate.
            if self._agent.is_kernel_creation_in_flight(kernel_id):
                continue
            first_seen = self._unknown_since.get(kernel_id, since_now)
            unknown[kernel_id] = first_seen
            if since_now - first_seen >= ORPHAN_KERNEL_THRESHOLD_SEC:
                # Not suppressed: the manager may still hold this session, e.g. in CREATING.
                orphan_kernels.append((kernel_id, kernel.session_id, False))
                log.debug(
                    "orphan kernel detected, never checked by a sweeping manager",
                    kernel_id=kernel_id,
                    threshold_sec=ORPHAN_KERNEL_THRESHOLD_SEC,
                )
        # Keep only what is still unknown; a kernel checked since starts over.
        self._unknown_since = unknown

        # 6. Cleanup orphan kernels via lifecycle event
        for kernel_id, session_id, suppress_events in orphan_kernels:
            try:
                log.info("orphan kernel cleaning up", kernel_id=kernel_id, session_id=session_id)
                await self._agent.inject_container_lifecycle_event(
                    kernel_id,
                    session_id,
                    LifecycleEvent.DESTROY,
                    KernelLifecycleEventReason.NOT_FOUND_IN_MANAGER,
                    suppress_events=suppress_events,
                )
            except Exception:
                log.exception(
                    "orphan kernel cleanup failed", kernel_id=kernel_id, session_id=session_id
                )

    @staticmethod
    def _was_dropped_by_manager(status: KernelStatus, agent_last_check: int | None) -> bool:
        """Rule (a): the manager checked this kernel once, then stopped while still checking us."""
        if status.last_check is None or agent_last_check is None:
            return False
        return status.last_check < agent_last_check - ORPHAN_KERNEL_THRESHOLD_SEC

    @override
    def observe_interval(self) -> float:
        return 300.0  # 5 minutes

    @classmethod
    @override
    def timeout(cls) -> float | None:
        return 30.0  # 30 seconds

    @override
    async def cleanup(self) -> None:
        pass
