from abc import ABC, abstractmethod
from collections.abc import Mapping
from typing import Any


class AbstractConfigLoader(ABC):
    @abstractmethod
    async def load(self) -> Mapping[str, Any]:
        raise NotImplementedError
