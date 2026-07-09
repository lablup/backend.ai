from abc import ABC, abstractmethod
from collections import defaultdict
from collections.abc import Sequence

from ai.backend.manager.data.sokovan import SessionWorkload, SystemSnapshot


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
        priority_workloads: defaultdict[int, list[SessionWorkload]] = defaultdict(list)
        for workload in workloads:
            priority_workloads[workload.priority].append(workload)

        result: list[SessionWorkload] = []
        for priority in sorted(priority_workloads.keys(), reverse=True):
            sequenced = await self._workload_sequencer.sequence(
                resource_group, system_snapshot, priority_workloads[priority]
            )
            result.extend(sequenced)
        return result
