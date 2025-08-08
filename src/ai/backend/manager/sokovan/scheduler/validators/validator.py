from abc import ABC
from collections.abc import Iterable

from ai.backend.manager.sokovan.scheduler.types import SessionWorkload, SystemSnapshot

from .exceptions import MultipleValidationErrors, SchedulingValidationError


class ValidatorRule(ABC):
    """
    An abstract base class for validator rules.
    Subclasses should implement the `validate` method to apply specific validation logic.
    """

    def validate(self, snapshot: SystemSnapshot, workload: SessionWorkload) -> None:
        """
        Validate a session workload against the system snapshot.

        Args:
            snapshot: The current system state snapshot
            workload: The session workload to validate

        Raises:
            SchedulingValidationError: If the workload fails validation
        """
        raise NotImplementedError("Subclasses should implement this method.")


class SchedulingValidator:
    """
    A class that validates session workloads against a set of rules.
    It applies each rule to the provided workload to ensure it meets the required conditions.
    """

    _rules: Iterable[ValidatorRule]

    def __init__(self, rules: Iterable[ValidatorRule]) -> None:
        self._rules = rules

    def validate(self, snapshot: SystemSnapshot, workload: SessionWorkload) -> None:
        """
        Validate a session workload against all configured rules.
        Collects all validation errors and raises them together.

        Args:
            snapshot: The current system state snapshot
            workload: The session workload to validate

        Raises:
            SchedulingValidationError: If exactly one rule fails
            MultipleValidationErrors: If multiple rules fail
        """
        errors: list[SchedulingValidationError] = []

        for rule in self._rules:
            try:
                rule.validate(snapshot, workload)
            except SchedulingValidationError as e:
                errors.append(e)

        if errors:
            if len(errors) == 1:
                raise errors[0]
            else:
                raise MultipleValidationErrors(errors)
