from abc import ABC, abstractmethod
from collections.abc import Mapping
from typing import Any


class AbstractConfigLoader(ABC):
    @abstractmethod
    async def load(self) -> Mapping[str, Any]:
        raise NotImplementedError

    @property
    def source_name(self) -> str:
        """Human-readable loader identifier for debugging/tracking."""
        return type(self).__name__


class AbstractConfigWatcher(ABC):
    @abstractmethod
    async def watch(self) -> Mapping[str, Any]:
        raise NotImplementedError
