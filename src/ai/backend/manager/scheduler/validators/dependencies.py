from ai.backend.common.types import SessionResult
from ai.backend.manager.errors.scheduler import DependencyNotMetError
from ai.backend.manager.models.session import SessionStatus
from ai.backend.manager.scheduler.validators.types import ValidatorContext
from ai.backend.manager.scheduler.validators.validator import SchedulerValidator


class DependenciesValidator(SchedulerValidator):
    """Validator to check if all dependency sessions have finished successfully."""

    @property
    def name(self) -> str:
        return "dependencies"

    async def validate(self, context: ValidatorContext) -> None:
        """
        Check if all dependency sessions have finished successfully.

        Raises:
            DependencyNotMetError: If any dependency session hasn't finished successfully
        """
        pending_dependencies = []

        for dep in context.session_dependencies:
            if (
                SessionResult(dep.result) != SessionResult.SUCCESS
                or SessionStatus(dep.status) != SessionStatus.TERMINATED
            ):
                pending_dependencies.append(dep)

        if pending_dependencies:
            dependency_names = ", ".join(f"{dep.name} ({dep.id})" for dep in pending_dependencies)
            raise DependencyNotMetError(
                f"Waiting dependency sessions to finish as success. ({dependency_names})"
            )
