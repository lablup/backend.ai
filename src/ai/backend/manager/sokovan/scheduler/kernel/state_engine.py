"""
Kernel state management engine for Sokovan scheduler.

This module handles kernel lifecycle events and state transitions.
All database operations go through the repository pattern.
"""

import logging

from ai.backend.common.events.event_types.kernel.anycast import (
    KernelCancelledAnycastEvent,
    KernelCreatingAnycastEvent,
    KernelHeartbeatEvent,
    KernelPreparingAnycastEvent,
    KernelPullingAnycastEvent,
    KernelStartedAnycastEvent,
    KernelTerminatedAnycastEvent,
)
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.repositories.scheduler import SchedulerRepository

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class KernelStateEngine:
    """
    Manages kernel state transitions in the Sokovan scheduler.

    This class handles kernel lifecycle events such as pulling, creating,
    running, terminating, etc. It only manages kernel state changes and
    does not directly update session states.

    Session state updates are handled separately by the scheduler to implement
    the mark-execute pattern for better scalability.
    """

    _repository: SchedulerRepository

    def __init__(self, repository: SchedulerRepository):
        """
        Initialize the KernelStateEngine with a repository.

        :param repository: SchedulerRepository for database operations
        """
        self._repository = repository

    async def mark_kernel_pulling(
        self,
        event: KernelPullingAnycastEvent,
    ) -> bool:
        """
        Mark a kernel as PULLING when starting to pull its image.

        :param event: The kernel pulling event
        :return: True if the update was successful
        """
        log.debug("Marking kernel {} as PULLING", event.kernel_id)

        # Use the repository's db_source to update kernel status
        success = await self._repository._db_source.update_kernel_status_pulling(
            event.kernel_id, event.session_id, event.reason
        )

        if success:
            log.info("Kernel {} marked as PULLING", event.kernel_id)
        else:
            log.warning(
                "Failed to mark kernel {} as PULLING - may not be in SCHEDULED state",
                event.kernel_id,
            )

        return success

    async def mark_kernel_creating(
        self,
        event: KernelCreatingAnycastEvent,
    ) -> bool:
        """
        Mark a kernel as CREATING when starting to create its container.

        :param event: The kernel creating event
        :return: True if the update was successful
        """
        log.debug("Marking kernel {} as CREATING", event.kernel_id)

        success = await self._repository._db_source.update_kernel_status_creating(
            event.kernel_id, event.session_id, event.reason
        )

        if success:
            log.info("Kernel {} marked as CREATING", event.kernel_id)
        else:
            log.warning(
                "Failed to mark kernel {} as CREATING - may not be in PULLING state",
                event.kernel_id,
            )

        return success

    async def mark_kernel_running(
        self,
        event: KernelStartedAnycastEvent,
    ) -> bool:
        """
        Mark a kernel as RUNNING when its container is successfully started.

        :param event: The kernel started event with creation info
        :return: True if the update was successful
        """
        log.debug("Marking kernel {} as RUNNING", event.kernel_id)

        success = await self._repository._db_source.update_kernel_status_running(
            event.kernel_id,
            event.session_id,
            event.reason,
            dict(event.creation_info) if event.creation_info else {},
        )

        if success:
            log.info("Kernel {} marked as RUNNING", event.kernel_id)
        else:
            log.warning(
                "Failed to mark kernel {} as RUNNING - may not be in CREATING state",
                event.kernel_id,
            )

        return success

    async def mark_kernel_preparing(
        self,
        event: KernelPreparingAnycastEvent,
    ) -> bool:
        """
        Mark a kernel as PREPARING when starting preparation phase.

        :param event: The kernel preparing event
        :return: True if the update was successful
        """
        log.debug("Marking kernel {} as PREPARING", event.kernel_id)

        success = await self._repository._db_source.update_kernel_status_preparing(
            event.kernel_id, event.session_id
        )

        if success:
            log.info("Kernel {} marked as PREPARING", event.kernel_id)
        else:
            log.warning(
                "Failed to mark kernel {} as PREPARING - may not be in SCHEDULED state",
                event.kernel_id,
            )

        return success

    async def mark_kernel_cancelled(
        self,
        event: KernelCancelledAnycastEvent,
    ) -> bool:
        """
        Mark a kernel as CANCELLED when it's cancelled before running.

        :param event: The kernel cancelled event
        :return: True if the update was successful
        """
        log.debug("Marking kernel {} as CANCELLED: {}", event.kernel_id, event.reason)

        success = await self._repository._db_source.update_kernel_status_cancelled(
            event.kernel_id, event.session_id, event.reason
        )

        if success:
            log.info("Kernel {} marked as CANCELLED", event.kernel_id)
        else:
            log.warning(
                "Failed to mark kernel {} as CANCELLED - may already be running or terminated",
                event.kernel_id,
            )

        return success

    async def mark_kernel_terminated(
        self,
        event: KernelTerminatedAnycastEvent,
    ) -> bool:
        """
        Mark a kernel as TERMINATED when it's terminated.

        :param event: The kernel terminated event
        :return: True if the update was successful
        """
        log.debug("Marking kernel {} as TERMINATED: {}", event.kernel_id, event.reason)

        success = await self._repository._db_source.update_kernel_status_terminated(
            event.kernel_id, event.session_id, event.reason, event.exit_code
        )

        if success:
            log.info("Kernel {} marked as TERMINATED", event.kernel_id)
        else:
            log.warning(
                "Failed to mark kernel {} as TERMINATED - may not be in TERMINATING state",
                event.kernel_id,
            )

        return success

    async def update_kernel_heartbeat(
        self,
        event: KernelHeartbeatEvent,
    ) -> bool:
        """
        Update the heartbeat timestamp for a running kernel.

        :param event: The kernel heartbeat event
        :return: True if the update was successful
        """
        log.trace("Updating heartbeat for kernel {}", event.kernel_id)

        success = await self._repository._db_source.update_kernel_heartbeat(event.kernel_id)

        if not success:
            log.warning(
                "Failed to update heartbeat for kernel {} - may not be in RUNNING state",
                event.kernel_id,
            )

        return success
