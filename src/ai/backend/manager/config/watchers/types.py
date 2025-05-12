from abc import ABC, abstractmethod
from collections.abc import Mapping
from typing import Any


class AbstractConfigWatcher(ABC):
    @abstractmethod
    async def watch(self) -> Mapping[str, Any]:
        raise NotImplementedError
