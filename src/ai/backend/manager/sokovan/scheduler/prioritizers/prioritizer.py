from abc import ABC, abstractmethod
from collections.abc import Sequence

from ..types import SessionWorkload, SystemSnapshot


class SchedulingPrioritizer(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        """
        The name of the prioritizer.
        This should be overridden by subclasses to provide a unique identifier.
        """
        raise NotImplementedError("Subclasses should implement this property.")

    @abstractmethod
    async def prioritize(
        self, system_snapshot: SystemSnapshot, workload: Sequence[SessionWorkload]
    ) -> Sequence[SessionWorkload]:
        """
        Prioritize a collection of workloads based on specific criteria.
        :param workload: An iterable of SessionWorkload objects to prioritize.
        :return: An iterable of prioritized SessionWorkload objects.
        """
        raise NotImplementedError("Subclasses should implement this method.")
