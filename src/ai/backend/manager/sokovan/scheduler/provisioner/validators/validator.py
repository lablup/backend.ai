from abc import ABC, abstractmethod
from collections.abc import Iterable

from ai.backend.manager.sokovan.scheduler.types import (
    SchedulingPredicate,
    SessionWorkload,
    SystemSnapshot,
)

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
        passed_phases: list[SchedulingPredicate],
        failed_phases: list[SchedulingPredicate],
    ) -> None:
        """
        Validate a session workload and update passed/failed phases lists.

        Args:
            snapshot: The current system state snapshot
            workload: The session workload to validate
            passed_phases: List to update with passed validation phases
            failed_phases: List to update with failed validation phases

        Raises:
            SchedulingValidationError: If any validation fails
        """
        errors: list[SchedulingValidationError] = []

        for rule in self._rules:
            try:
                rule.validate(snapshot, workload)
                # Validation passed - add to the passed list
                passed_phases.append(
                    SchedulingPredicate(name=rule.name(), msg=rule.success_message())
                )
            except SchedulingValidationError as e:
                # Validation failed - add to failed list and collect error
                failed_phases.append(SchedulingPredicate(name=rule.name(), msg=str(e)))
                errors.append(e)

        # If there were any failures, raise the appropriate exception
        if errors:
            if len(errors) == 1:
                raise errors[0]
            else:
                raise MultipleValidationErrors(errors)
