from abc import ABC, abstractmethod
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from pydantic import Field


class AbstractConfigLoader(ABC):
    @abstractmethod
    async def load(self) -> Mapping[str, Any]:
        raise NotImplementedError()


@dataclass
class ConfigTypeField:
    # TODO: Add type
    type: Any
    value: Any
    paths: list[str] = Field(gt=0)
