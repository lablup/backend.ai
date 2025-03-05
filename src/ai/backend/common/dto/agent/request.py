from abc import ABC
from dataclasses import dataclass
from typing import TypeVar

T = TypeVar("T")


@dataclass
class AbstractAgentRequest(ABC): ...


@dataclass
class PurgeImageRequest:
    images: list[str]
