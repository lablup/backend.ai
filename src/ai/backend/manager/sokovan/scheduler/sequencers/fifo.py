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
        The name of the sequencer.
        This should be overridden by subclasses to provide a unique identifier.
        """
        return "FIFO-scheduling-sequencer"

    @override
    async def sequence(
        self, system_snapshot: SystemSnapshot, workloads: Sequence[SessionWorkload]
    ) -> Sequence[SessionWorkload]:
        """
        Sequence the workloads in FIFO order.
        :param system_snapshot: The current system snapshot containing resource state.
        :param workloads: A sequence of SessionWorkload objects to sequence.
        :return: A sequence of SessionWorkload objects in FIFO order.
        """
        return workloads  # Return the workloads in the order they were received
