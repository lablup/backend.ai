from collections.abc import Sequence
from typing import override

from ..types import SessionWorkload, SystemSnapshot
from .prioritizer import SchedulingPrioritizer


class LIFOSchedulingPrioritizer(SchedulingPrioritizer):
    """
    A scheduling prioritizer that implements Last In, First Out (LIFO) prioritization.
    This prioritizer will prioritize the most recently added workloads first.
    """

    @property
    @override
    def name(self) -> str:
        """
        The name of the prioritizer.
        This should be overridden by subclasses to provide a unique identifier.
        """
        return "LIFO-scheduling-prioritizer"

    @override
    async def prioritize(
        self, system_snapshot: SystemSnapshot, workloads: Sequence[SessionWorkload]
    ) -> Sequence[SessionWorkload]:
        """
        Prioritize the workloads in LIFO order.
        :param workload: A sequence of SessionWorkload objects to prioritize.
        :return: A sequence of SessionWorkload objects in LIFO order.
        """
        if not workloads:
            return []
        return list(reversed(workloads))  # Reverse the order to implement LIFO
