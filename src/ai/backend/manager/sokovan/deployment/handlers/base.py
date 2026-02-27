from abc import abstractmethod
from collections.abc import Sequence

from ai.backend.manager.data.deployment.types import (
    DeploymentInfo,
    DeploymentStatusTransitions,
)
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
    def lock_id(self) -> LockID | None:
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
    def status_transitions(cls) -> DeploymentStatusTransitions:
        """Define state transitions for different handler outcomes (BEP-1030).

        Returns:
            DeploymentStatusTransitions defining what lifecycle to transition to for
            success and failure outcomes.

        Note:
            - None value: Don't change the deployment lifecycle
        """
        raise NotImplementedError("Subclasses must implement status_transitions()")

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
