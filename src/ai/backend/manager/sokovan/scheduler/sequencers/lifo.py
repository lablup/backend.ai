from collections.abc import Sequence
from typing import override

from ..types import SessionWorkload, SystemSnapshot
from .sequencer import WorkloadSequencer


class LIFOSequencer(WorkloadSequencer):
    """
    A scheduling sequencer that implements Last In, First Out (LIFO) sequencing.
    This sequencer will sequence the most recently added workloads first.
    """

    @property
    @override
    def name(self) -> str:
        """
        The name of the sequencer.
        This should be overridden by subclasses to provide a unique identifier.
        """
        return "LIFO-scheduling-sequencer"

    @override
    async def sequence(
        self, system_snapshot: SystemSnapshot, workloads: Sequence[SessionWorkload]
    ) -> Sequence[SessionWorkload]:
        """
        Sequence the workloads in LIFO order.
        :param system_snapshot: The current system snapshot containing resource state.
        :param workloads: A sequence of SessionWorkload objects to sequence.
        :return: A sequence of SessionWorkload objects in LIFO order.
        """
        if not workloads:
            return []
        return list(reversed(workloads))  # Reverse the order to implement LIFO
