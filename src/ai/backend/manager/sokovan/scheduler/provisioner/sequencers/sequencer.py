from abc import ABC, abstractmethod
from collections.abc import Sequence

from ai.backend.manager.sokovan.data import SessionWorkload, SystemSnapshot


class WorkloadSequencer(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        """
        Return the sequencer name for predicates.
        """
        raise NotImplementedError

    @abstractmethod
    def success_message(self) -> str:
        """
        Return a message describing successful sequencing.
        """
        raise NotImplementedError

    @abstractmethod
    async def sequence(
        self,
        resource_group: str,
        system_snapshot: SystemSnapshot,
        workloads: Sequence[SessionWorkload],
    ) -> Sequence[SessionWorkload]:
        """
        Sequence the workloads based on the system snapshot.

        :param resource_group: The resource group (scaling group) name.
        :param system_snapshot: The current system snapshot containing resource state.
        :param workloads: A sequence of SessionWorkload objects to order.
        :return: A sequence of SessionWorkload objects ordered by the sequencer's logic.
        """
        raise NotImplementedError("Subclasses should implement this method.")


class SchedulingSequencer:
    _workload_sequencer: WorkloadSequencer

    def __init__(self, workload_sequencer: WorkloadSequencer) -> None:
        self._workload_sequencer = workload_sequencer

    @property
    def name(self) -> str:
        """
        Return the sequencer name for predicates.
        """
        return self._workload_sequencer.name

    def success_message(self) -> str:
        """
        Return a message describing successful sequencing.
        """
        return self._workload_sequencer.success_message()

    async def sequence(
        self,
        resource_group: str,
        system_snapshot: SystemSnapshot,
        workloads: Sequence[SessionWorkload],
    ) -> Sequence[SessionWorkload]:
        """
        Sequence the workloads based on their priority using the configured workload sequencer.

        :param resource_group: The resource group (scaling group) name.
        :param system_snapshot: The current system snapshot containing resource state.
        :param workloads: A sequence of SessionWorkload objects to order.
        :return: A sequence of SessionWorkload objects ordered by priority and the sequencer's logic.
        """
        priorities = {s.priority for s in workloads}
        top_priority = max(priorities)
        filtered_workloads = [*filter(lambda s: s.priority == top_priority, workloads)]

        return await self._workload_sequencer.sequence(
            resource_group, system_snapshot, filtered_workloads
        )
