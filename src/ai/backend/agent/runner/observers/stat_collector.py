import logging

from ai.backend.logging.utils import BraceStyleAdapter

from ...stats import StatContext
from ..observer import AbstractObserver

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class NodeStatCollectorObserver(AbstractObserver):
    """
    Collects statistics from the agent and stores them in a dictionary.
    """

    _stat_ctx: StatContext

    def __init__(self, stat_ctx: StatContext):
        self._stat_ctx = stat_ctx

    async def observe(self) -> None:
        """
        Observe the state of the system.
        """
        await self._stat_ctx.collect_node_stat()

    async def observe_interval(self) -> float:
        """
        Return the interval at which to observe the system.
        """
        return 5.0

    async def close(self) -> None:
        # No resources to clean up
        pass
