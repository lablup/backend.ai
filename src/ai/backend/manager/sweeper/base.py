import abc

from ..models.utils import ExtendedAsyncSAEngine
from ..registry import AgentRegistry

DEFAULT_SWEEP_INTERVAL_SEC = 60.0


class AbstractSweeper(abc.ABC):
    _db: ExtendedAsyncSAEngine
    _registry: AgentRegistry

    def __init__(self, db: ExtendedAsyncSAEngine, registry: AgentRegistry, *args, **kwargs) -> None:
        self._db = db
        self._registry = registry

    @abc.abstractmethod
    async def sweep(self) -> None:
        raise NotImplementedError
