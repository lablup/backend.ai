from collections.abc import Sequence
from typing import override

from ..types import SessionWorkload, SystemSnapshot
from .sequencer import WorkloadSequencer


class FIFOSequencer(WorkloadSequencer):
    """
    A scheduling sequencer that implements First In, First Out (FIFO) sequencing.
    This sequencer will sequence the oldest workloads first.
    """

    @property
    @override
    def name(self) -> str:
        """
        Return the sequencer name for predicates.
        """
        return "FIFOSequencer"

    @override
    def success_message(self) -> str:
        """
        Return a message describing successful sequencing.
        """
        return "Sessions sequenced in first-in-first-out order"

    @override
    def sequence(
        self, system_snapshot: SystemSnapshot, workloads: Sequence[SessionWorkload]
    ) -> Sequence[SessionWorkload]:
        """
        Sequence the workloads in FIFO order.
        :param system_snapshot: The current system snapshot containing resource state.
        :param workloads: A sequence of SessionWorkload objects to sequence.
        :return: A sequence of SessionWorkload objects in FIFO order.
        """
        return workloads  # Return the workloads in the order they were received
