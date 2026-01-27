from abc import ABC, abstractmethod
from collections.abc import Iterable

from ai.backend.common.types import SessionId
from ai.backend.manager.sokovan.data import (
    SessionWorkload,
    SystemSnapshot,
)
from ai.backend.manager.sokovan.recorder import RecorderContext

from .exceptions import MultipleValidationErrors, SchedulingValidationError


class ValidatorRule(ABC):
    """
    An abstract base class for validator rules.
    Subclasses should implement the `validate` method to apply specific validation logic.
    """

    @abstractmethod
    def name(self) -> str:
        """Return the validator name for predicates."""
        raise NotImplementedError

    @abstractmethod
    def success_message(self) -> str:
        """Return a message describing successful validation."""
        raise NotImplementedError

    @abstractmethod
    def validate(self, snapshot: SystemSnapshot, workload: SessionWorkload) -> None:
        """
        Validate a session workload against the system snapshot.

        Args:
            snapshot: The current system state snapshot
            workload: The session workload to validate

        Raises:
            SchedulingValidationError: If the workload fails validation
        """
        raise NotImplementedError


class SchedulingValidator:
    """
    A class that validates session workloads against a set of rules.
    It applies each rule to the provided workload to ensure it meets the required conditions.
    """

    _rules: Iterable[ValidatorRule]

    def __init__(self, rules: Iterable[ValidatorRule]) -> None:
        self._rules = rules

    def validate(
        self,
        snapshot: SystemSnapshot,
        workload: SessionWorkload,
    ) -> None:
        """
        Validate a session workload using the recorder context.

        Each validation rule is recorded as a step within the current phase.
        The recorder must be accessible via RecorderContext.current_pool().

        Args:
            snapshot: The current system state snapshot
            workload: The session workload to validate

        Raises:
            SchedulingValidationError: If any validation fails
        """
        pool = RecorderContext[SessionId].current_pool()
        recorder = pool.recorder(workload.session_id)
        errors: list[SchedulingValidationError] = []

        for rule in self._rules:
            try:
                with recorder.step(rule.name(), success_detail=rule.success_message()):
                    rule.validate(snapshot, workload)
            except SchedulingValidationError as e:
                errors.append(e)

        # If there were any failures, raise the appropriate exception
        if errors:
            if len(errors) == 1:
                raise errors[0]
            raise MultipleValidationErrors(errors)
