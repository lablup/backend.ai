from abc import ABC
from collections.abc import Iterable

from ai.backend.manager.sokovan.scheduler.types import SessionWorkload, SystemSnapshot


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

        Args:
            snapshot: The current system state snapshot
            workload: The session workload to validate

        Raises:
            SchedulingValidationError: If any rule fails
        """
        for rule in self._rules:
            rule.validate(snapshot, workload)
