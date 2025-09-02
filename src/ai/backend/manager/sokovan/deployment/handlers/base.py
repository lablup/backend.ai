from abc import abstractmethod
from collections.abc import Sequence
from typing import Optional

from ai.backend.manager.data.deployment.types import DeploymentInfo
from ai.backend.manager.data.model_serving.types import EndpointLifecycle
from ai.backend.manager.defs import LockID
from ai.backend.manager.sokovan.deployment.types import DeploymentExecutionResult


class DeploymentHandler:
    """Base class for deployment operation handlers using the generic interface."""

    @classmethod
    @abstractmethod
    def name(cls) -> str:
        """Get the name of the handler."""
        raise NotImplementedError("Subclasses must implement name()")

    @property
    @abstractmethod
    def lock_id(self) -> Optional[LockID]:
        """Get the lock ID for this handler.

        Returns:
            LockID to acquire before execution, or None if no lock needed
        """
        raise NotImplementedError("Subclasses must implement lock_id")

    @classmethod
    @abstractmethod
    def target_statuses(cls) -> list[EndpointLifecycle]:
        """Get the target deployment statuses for this handler.

        Returns:
            List of deployment statuses that this handler targets
        """
        raise NotImplementedError("Subclasses must implement target_statuses()")

    @classmethod
    @abstractmethod
    def next_status(cls) -> Optional[EndpointLifecycle]:
        """Get the next deployment status after this handler's operation.

        Returns:
            The next deployment status
        """
        raise NotImplementedError("Subclasses must implement next_status()")

    @classmethod
    @abstractmethod
    def failure_status(cls) -> Optional[EndpointLifecycle]:
        """Get the failure deployment status if applicable.

        Returns:
            The failure deployment status, or None if not applicable
        """
        raise NotImplementedError("Subclasses must implement failure_status()")

    @abstractmethod
    async def execute(self, deployments: Sequence[DeploymentInfo]) -> DeploymentExecutionResult:
        """Execute the scheduling operation.

        Returns:
            Result of the scheduling operation
        """
        raise NotImplementedError("Subclasses must implement execute()")

    @abstractmethod
    async def post_process(self, result: DeploymentExecutionResult) -> None:
        """Handle post-processing after the operation.

        Args:
            result: The result from execute()
        """
        raise NotImplementedError("Subclasses must implement post_process()")
