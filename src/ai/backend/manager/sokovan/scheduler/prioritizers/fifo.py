from collections.abc import Sequence
from typing import override

from ..types import SessionWorkload, SystemSnapshot
from .prioritizer import SchedulingPrioritizer


class FIFOSchedulingPrioritizer(SchedulingPrioritizer):
    """
    A scheduling prioritizer that implements First In, First Out (FIFO) prioritization.
    This prioritizer will prioritize the oldest workloads first.
    """

    @property
    @override
    def name(self) -> str:
        """
        The name of the prioritizer.
        This should be overridden by subclasses to provide a unique identifier.
        """
        return "FIFO-scheduling-prioritizer"

    @override
    async def prioritize(
        self, system_snapshot: SystemSnapshot, workload: Sequence[SessionWorkload]
    ) -> Sequence[SessionWorkload]:
        """
        Prioritize the workloads in FIFO order.
        :param workload: A sequence of SessionWorkload objects to prioritize.
        :return: A sequence of SessionWorkload objects in FIFO order.
        """
        return workload  # Return the workloads in the order they were received
