from abc import ABC, abstractmethod
from collections import defaultdict
from collections.abc import Mapping, Sequence

from ai.backend.common.identifier.resource_group import ResourceGroupID
from ai.backend.manager.views.sokovan.snapshot import SystemSnapshot
from ai.backend.manager.views.sokovan.workload import SessionWorkload


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
        resource_group_id: ResourceGroupID,
        system_snapshot: SystemSnapshot,
        workloads: Sequence[SessionWorkload],
    ) -> Sequence[SessionWorkload]:
        """
        Sequence the workloads based on the system snapshot.

        :param resource_group_id: The resource group ID.
        :param system_snapshot: The current system snapshot containing resource state.
        :param workloads: A sequence of SessionWorkload objects to order.
        :return: A sequence of SessionWorkload objects ordered by the sequencer's logic.
        """
        raise NotImplementedError("Subclasses should implement this method.")


class SchedulingSequencer:
    """Sequences workloads with the strategy picked by scheduler name.

    Owns the strategy pool; callers only pass the scheduler name. Unknown
    names deliberately fall back to the pool's default strategy.
    """

    _pool: Mapping[str, WorkloadSequencer]

    def __init__(self, pool: Mapping[str, WorkloadSequencer]) -> None:
        self._pool = pool

    def strategy_name(self, scheduler: str) -> str:
        """Return the picked strategy's name for predicates."""
        return self._pool[scheduler].name

    def strategy_success_message(self, scheduler: str) -> str:
        """Return the picked strategy's success message."""
        return self._pool[scheduler].success_message()

    async def sequence(
        self,
        scheduler: str,
        resource_group_id: ResourceGroupID,
        system_snapshot: SystemSnapshot,
        workloads: Sequence[SessionWorkload],
    ) -> Sequence[SessionWorkload]:
        """
        Sequence the workloads priority-first, applying the picked strategy
        within each priority band.

        Higher ``workload.priority`` always comes first; the strategy's own
        ordering only decides ties within the same priority.

        :param scheduler: The scheduler name selecting the strategy.
        :param resource_group_id: The resource group ID.
        :param system_snapshot: The current system snapshot containing resource state.
        :param workloads: A sequence of SessionWorkload objects to order.
        :return: A sequence of SessionWorkload objects ordered by priority and the strategy's logic.
        """
        strategy = self._pool[scheduler]
        priority_workloads: defaultdict[int, list[SessionWorkload]] = defaultdict(list)
        for workload in workloads:
            priority_workloads[workload.priority].append(workload)

        result: list[SessionWorkload] = []
        for priority in sorted(priority_workloads.keys(), reverse=True):
            sequenced = await strategy.sequence(
                resource_group_id, system_snapshot, priority_workloads[priority]
            )
            result.extend(sequenced)
        return result
