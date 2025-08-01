from abc import ABC, abstractmethod


class SchedulingPolicy(ABC):
    """
    An abstract base class for scheduling policies.
    Subclasses should implement the `evaluate` method to apply specific scheduling logic.
    """

    @abstractmethod
    def evaluate(self, workload) -> None:
        raise NotImplementedError("Subclasses should implement this method.")
