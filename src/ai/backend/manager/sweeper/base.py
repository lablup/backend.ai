import abc

from ai.backend.common.metrics.metric import SweeperMetricObserver

from ..models.utils import ExtendedAsyncSAEngine
from ..registry import AgentRegistry

DEFAULT_SWEEP_INTERVAL_SEC = 60.0


class AbstractSweeper(abc.ABC):
    _db: ExtendedAsyncSAEngine
    _registry: AgentRegistry
    _sweeper_metric: SweeperMetricObserver

    def __init__(
        self,
        db: ExtendedAsyncSAEngine,
        registry: AgentRegistry,
        sweeper_metric: SweeperMetricObserver,
        *args,
        **kwargs,
    ) -> None:
        self._db = db
        self._registry = registry
        self._sweeper_metric = sweeper_metric

    @abc.abstractmethod
    async def sweep(self) -> None:
        raise NotImplementedError
