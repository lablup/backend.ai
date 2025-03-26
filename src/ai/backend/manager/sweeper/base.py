import abc
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..models.utils import ExtendedAsyncSAEngine
    from ..registry import AgentRegistry


class AbstractSweeper(abc.ABC):
    _db: ExtendedAsyncSAEngine
    _registry: AgentRegistry

    def __init__(self, db: ExtendedAsyncSAEngine, registry: AgentRegistry, *args, **kwargs) -> None:
        self._db = db
        self._registry = registry

    @abc.abstractmethod
    async def sweep(self) -> None:
        raise NotImplementedError
