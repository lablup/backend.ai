from abc import ABC, abstractmethod
from collections.abc import Sequence

from ..types import SessionWorkload, SystemSnapshot


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
    def sequence(
        self, system_snapshot: SystemSnapshot, workloads: Sequence[SessionWorkload]
    ) -> Sequence[SessionWorkload]:
        """
        Sequence the workloads based on the system snapshot.
        :param system_snapshot: The current system snapshot containing resource state.
        :param workloads: A sequence of SessionWorkload objects to order.
        :return: A sequence of SessionWorkload objects ordered by the sequencer's logic.
        """
        raise NotImplementedError("Subclasses should implement this method.")
