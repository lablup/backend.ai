from __future__ import annotations

import logging
import time
from typing import TYPE_CHECKING, Any, override

from ai.backend.agent.types import LifecycleEvent
from ai.backend.common.clients.valkey_client.valkey_schedule import ValkeyScheduleClient
from ai.backend.common.clients.valkey_client.valkey_schedule.client import (
    ORPHAN_KERNEL_THRESHOLD_SEC,
)
from ai.backend.common.events.event_types.kernel.types import KernelLifecycleEventReason
from ai.backend.common.observer.types import AbstractObserver
from ai.backend.common.types import KernelId, SessionId
from ai.backend.logging.utils import BraceStyleAdapter

if TYPE_CHECKING:
    from ai.backend.agent.agent import AbstractAgent

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class OrphanKernelCleanupObserver(AbstractObserver):
    """
    Observer that periodically detects and cleans up orphan kernels.

    Orphan kernels are containers that exist in Agent but have been
    terminated from Manager's DB. Until they are reaped they hold their
    allocation, so the agent and the manager disagree about this node's free
    capacity and the next session scheduled here fails with InsufficientResource.

    A kernel is an orphan when the manager is checking this agent but is not
    checking that kernel. Two shapes of that, and both have to be covered:

    - (a) The manager checked it once and has stopped:
      ``kernel.last_check < agent_last_check - THRESHOLD``. Needs
      ``agent_last_check``; where that is absent this rule simply does not
      apply, and rule (b) answers instead.
    - (b) The manager has never checked it at all -- no presence entry, one with
      no ``last_check``, or no ``agent_last_check`` for this agent because an
      outage outlasted its TTL. This is what an agent restart leaves behind: the
      presence key's TTL passes while the agent is down, and the agent's own
      presence observer then recreates it with a presence and no ``last_check``.
      Read as "not enough information" it was skipped forever, which is why a
      session terminated during a node outage kept its resources for good.

    "Never checked" is only meaningful after the manager has had the chance, so
    it is debounced: a kernel has to stay unknown across THRESHOLD seconds of
    this agent's uptime before it is reaped, which leaves a newly created kernel
    well clear of the manager's next sweep.

    Nothing is reaped unless the manager is LOOKING -- ``get_manager_sweep_epoch``
    is fresh. A manager that has stopped says nothing about any one kernel, and
    reaping on its silence would empty a healthy node.

    That signal is cluster-wide on purpose. ``agent_last_check`` cannot carry it:
    the manager stamps it only for agents that still have a kernel it knows
    about, so an agent whose ONLY kernel is the orphan never sees it advance --
    and a gate that waited for it to be fresh would deadlock against the very
    debounce it guards, on exactly the node the reap exists for.
    """

    _agent: AbstractAgent[Any, Any]
    _valkey_schedule_client: ValkeyScheduleClient
    #: ``kernel_id -> monotonic time`` this agent first saw a kernel of its own that the manager
    #: has never checked. The debounce above is measured from here.
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
        # 1. Get agent's last_check timestamp. Absent is not a reason to stop: it is what an
        #    outage longer than its 20-minute TTL leaves behind, and the manager only rewrites it
        #    for agents that still have a kernel it knows about -- so on the node this reap exists
        #    for, the one whose only kernel is the orphan, it never comes back. Stopping here left
        #    exactly that node uncleaned for good. It is only the basis for rule (a) below; rule
        #    (b) does not need it.
        agent_last_check = await self._valkey_schedule_client.get_agent_last_check(self._agent.id)

        # 2. Only act while the manager is looking at kernels at all. Its silence is about the
        #    manager, not about any kernel, and reaping on it would empty a healthy node. Read
        #    cluster-wide, NOT from this agent's own last_check: the manager stamps that only for
        #    agents that still have a kernel it knows about, so on the node this reap exists for
        #    -- the one whose only kernel is the orphan -- it never advances again.
        #    Redis' clock on both sides of the comparison, not this host's.
        sweep_epoch = await self._valkey_schedule_client.get_manager_sweep_epoch()
        if sweep_epoch is None:
            log.debug("Manager is not sweeping kernels, skipping orphan cleanup")
            self._unknown_since.clear()
            return
        now = await self._valkey_schedule_client.get_redis_time()
        if now - sweep_epoch > ORPHAN_KERNEL_THRESHOLD_SEC:
            log.debug(
                "Manager last swept kernels {}s ago, skipping orphan cleanup",
                now - sweep_epoch,
            )
            self._unknown_since.clear()
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
        orphan_kernels: list[tuple[KernelId, SessionId]] = []
        unknown: dict[KernelId, float] = {}
        since_now = time.monotonic()
        for kernel_id, kernel in kernel_registry.items():
            status = statuses.get(kernel_id)
            if (
                status is not None
                and status.last_check is not None
                and agent_last_check is not None
            ):
                # (a) The manager has checked this kernel at some point. It is an orphan once it
                # has stopped, while the agent as a whole is still being checked.
                if status.last_check < agent_last_check - ORPHAN_KERNEL_THRESHOLD_SEC:
                    orphan_kernels.append((kernel_id, kernel.session_id))
                    log.info(
                        "Detected orphan kernel: {} (last_check={}, agent_last_check={},"
                        " threshold={})",
                        kernel_id,
                        status.last_check,
                        agent_last_check,
                        ORPHAN_KERNEL_THRESHOLD_SEC,
                    )
                continue
            # (b) The manager has never checked this kernel, while it is sweeping. Either
            # it does not know the kernel (terminated while the agent was down, and the agent
            # re-adopted it on recovery) or it has not got to it yet. Debounced rather than
            # decided now, because only the second one resolves itself.
            first_seen = self._unknown_since.get(kernel_id, since_now)
            unknown[kernel_id] = first_seen
            if since_now - first_seen >= ORPHAN_KERNEL_THRESHOLD_SEC:
                orphan_kernels.append((kernel_id, kernel.session_id))
                log.info(
                    "Detected orphan kernel: {} (manager has never checked it in the {}s since"
                    " this agent first saw it, and is checking this agent)",
                    kernel_id,
                    ORPHAN_KERNEL_THRESHOLD_SEC,
                )
        # Only what is still unknown: a kernel the manager has since checked starts over if it
        # ever goes unknown again, and one that has gone is not tracked at all.
        self._unknown_since = unknown

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
    def timeout(cls) -> float | None:
        return 30.0  # 30 seconds

    @override
    async def cleanup(self) -> None:
        pass
