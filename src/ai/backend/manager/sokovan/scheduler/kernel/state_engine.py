"""
Kernel state management engine for Sokovan scheduler.

This module handles kernel lifecycle events and state transitions.
All database operations go through the repository pattern.
"""

import logging
from typing import Optional

from ai.backend.common.types import AgentId, KernelId, SessionId
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.repositories.scheduler import SchedulerRepository
from ai.backend.manager.sokovan.scheduler.types import KernelCreationInfo

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
        kernel_id: KernelId,
        reason: str,
    ) -> bool:
        """
        Mark a kernel as PULLING when starting to pull its image.

        :param kernel_id: The kernel ID
        :param reason: The reason for the state change
        :return: True if the update was successful
        """
        log.debug("Marking kernel {} as PULLING", kernel_id)

        # Use the repository to update kernel status
        return await self._repository.update_kernel_status_pulling(kernel_id, reason)

    async def mark_kernel_creating(
        self,
        kernel_id: KernelId,
        reason: str,
    ) -> bool:
        """
        Mark a kernel as CREATING when starting to create its container.

        :param kernel_id: The kernel ID
        :param reason: The reason for the state change
        :return: True if the update was successful
        """
        log.debug("Marking kernel {} as CREATING", kernel_id)

        return await self._repository.update_kernel_status_creating(kernel_id, reason)

    async def mark_kernel_running(
        self,
        kernel_id: KernelId,
        reason: str,
        creation_info: KernelCreationInfo,
    ) -> bool:
        """
        Mark a kernel as RUNNING when its container is successfully started.

        :param kernel_id: The kernel ID
        :param reason: The reason for the state change
        :param creation_info: Creation information as dataclass
        :return: True if the update was successful
        """
        log.debug("Marking kernel {} as RUNNING", kernel_id)

        return await self._repository.update_kernel_status_running(
            kernel_id,
            reason,
            creation_info,
        )

    async def mark_kernel_preparing(
        self,
        kernel_id: KernelId,
    ) -> bool:
        """
        Mark a kernel as PREPARING when starting preparation phase.

        :param kernel_id: The kernel ID
        :return: True if the update was successful
        """
        log.debug("Marking kernel {} as PREPARING", kernel_id)

        return await self._repository.update_kernel_status_preparing(kernel_id)

    async def mark_kernel_cancelled(
        self,
        kernel_id: KernelId,
        session_id: SessionId,
        reason: str,
    ) -> bool:
        """
        Mark a kernel as CANCELLED when it's cancelled before running.
        Also checks if the session should be cancelled when all kernels are cancelled.

        :param kernel_id: The kernel ID
        :param session_id: The session ID (used for session cancellation check)
        :param reason: The reason for cancellation
        :return: True if the update was successful
        """
        log.debug("Marking kernel {} as CANCELLED: {}", kernel_id, reason)

        success = await self._repository.update_kernel_status_cancelled(kernel_id, reason)

        if success:
            # Check if the session should be cancelled when all kernels are cancelled
            await self._repository.check_and_cancel_session_if_needed(session_id)

        return success

    async def mark_kernel_terminated(
        self,
        kernel_id: KernelId,
        reason: str,
        exit_code: Optional[int] = None,
    ) -> bool:
        """
        Mark a kernel as TERMINATED when it's terminated.

        :param kernel_id: The kernel ID
        :param reason: The reason for termination
        :param exit_code: Optional exit code
        :return: True if the update was successful
        """
        log.debug("Marking kernel {} as TERMINATED: {}", kernel_id, reason)

        return await self._repository.update_kernel_status_terminated(kernel_id, reason, exit_code)

    async def update_kernel_heartbeat(
        self,
        kernel_id: KernelId,
    ) -> bool:
        """
        Update the heartbeat timestamp for a running kernel.

        :param kernel_id: The kernel ID
        :return: True if the update was successful
        """
        log.trace("Updating heartbeat for kernel {}", kernel_id)

        return await self._repository.update_kernel_heartbeat(kernel_id)

    async def update_kernels_to_pulling_for_image(
        self,
        agent_id: AgentId,
        image: str,
        image_ref: Optional[str] = None,
    ) -> None:
        """
        Update kernel status from PREPARING to PULLING for the specified image on an agent.

        :param agent_id: The agent ID where kernels should be updated
        :param image: The image name to match kernels
        :param image_ref: Optional image reference
        """
        log.debug(
            "Updating kernels to PULLING for agent:{} image:{}",
            agent_id,
            image,
        )

        await self._repository.update_kernels_to_pulling_for_image(agent_id, image, image_ref)

    async def update_kernels_to_prepared_for_image(
        self,
        agent_id: AgentId,
        image: str,
        image_ref: Optional[str] = None,
    ) -> int:
        """
        Update kernel status to PREPARED for the specified image on an agent.
        Updates kernels in both PULLING and PREPARING states.

        :param agent_id: The agent ID where kernels should be updated
        :param image: The image name to match kernels
        :param image_ref: Optional image reference
        :return: The number of kernels updated to PREPARED state
        """
        return await self._repository.update_kernels_to_prepared_for_image(
            agent_id, image, image_ref
        )

    async def cancel_kernels_for_failed_image(
        self,
        agent_id: AgentId,
        image: str,
        error_msg: str,
        image_ref: Optional[str] = None,
    ) -> None:
        """
        Cancel kernels for an image that failed to be available on an agent.

        :param agent_id: The agent ID where the image is unavailable
        :param image: The image name that failed
        :param error_msg: The error message to include in status
        :param image_ref: Optional image reference
        """
        log.warning(
            "Cancelling kernels for failed image on agent:{} image:{}, msg:{}",
            agent_id,
            image,
            error_msg,
        )

        await self._repository.cancel_kernels_for_failed_image(
            agent_id, image, error_msg, image_ref
        )
