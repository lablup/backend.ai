from abc import ABC, abstractmethod
from collections.abc import Sequence

from ai.backend.manager.sokovan.scheduler.types import SessionWorkload


class SchedulingPrioritizer(ABC):
    @abstractmethod
    async def prioritize(self, workload: Sequence[SessionWorkload]) -> Sequence[SessionWorkload]:
        """
        Prioritize a collection of workloads based on specific criteria.
        :param workload: An iterable of SessionWorkload objects to prioritize.
        :return: An iterable of prioritized SessionWorkload objects.
        """
        raise NotImplementedError("Subclasses should implement this method.")
