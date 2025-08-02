from abc import ABC
from collections.abc import Iterable

from ai.backend.manager.sokovan.scheduler.types import SessionWorkload


class ValidatorRule(ABC):
    """
    An abstract base class for validator rules.
    Subclasses should implement the `validate` method to apply specific validation logic.
    """

    def validate(self, workload: SessionWorkload) -> None:
        raise NotImplementedError("Subclasses should implement this method.")


class SchedulingValidator:
    """
    A class that validates session workloads against a set of rules.
    It applies each rule to the provided workload to ensure it meets the required conditions.
    """

    _rules: Iterable[ValidatorRule]

    def __init__(self, rules: Iterable[ValidatorRule]) -> None:
        self._rules = rules

    def validate(self, workload: SessionWorkload) -> None:
        for rule in self._rules:
            rule.validate(workload)
