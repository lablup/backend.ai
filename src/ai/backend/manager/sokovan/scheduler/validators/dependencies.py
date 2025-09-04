"""Validator for session dependencies."""

from ai.backend.common.types import SessionResult
from ai.backend.manager.data.session.types import SessionStatus
from ai.backend.manager.sokovan.scheduler.types import SessionWorkload, SystemSnapshot

from .exceptions import DependenciesNotSatisfied
from .validator import ValidatorRule


class DependenciesValidator(ValidatorRule):
    """
    Check if all dependent sessions have completed successfully.
    This corresponds to check_dependencies predicate.
    """

    def name(self) -> str:
        """Return the validator name for predicates."""
        return "SessionDependenciesValidator"

    def success_message(self) -> str:
        """Return a message describing successful validation."""
        return "All dependent sessions have completed successfully"

    def validate(self, snapshot: SystemSnapshot, workload: SessionWorkload) -> None:
        # Get dependencies for this session
        dependencies = snapshot.session_dependencies.by_session.get(workload.session_id, [])

        # Check if all dependencies are satisfied
        pending_dependencies = []
        for dep in dependencies:
            if (
                dep.dependency_result != SessionResult.SUCCESS
                or dep.dependency_status != SessionStatus.TERMINATED
            ):
                pending_dependencies.append(dep)

        if pending_dependencies:
            dep_names = [
                f"{dep.dependency_name} ({dep.depends_on})" for dep in pending_dependencies
            ]
            raise DependenciesNotSatisfied(
                f"Waiting dependency sessions to finish as success. ({', '.join(dep_names)})"
            )
