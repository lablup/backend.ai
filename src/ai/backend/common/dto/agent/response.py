from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass
from typing import Optional, Self, TypeVar, override

T = TypeVar("T")


@dataclass
class AbstractAgentResp(ABC):
    @abstractmethod
    def as_dict(self) -> dict:
        raise NotImplementedError


@dataclass
class PurgeImageResp(AbstractAgentResp):
    image: str
    error: Optional[str] = None

    @override
    def as_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def success(cls, image: str) -> Self:
        return cls(image)

    @classmethod
    def failure(cls, image: str, error: str) -> Self:
        return cls(image, error)


@dataclass
class PurgeImagesResp(AbstractAgentResp):
    responses: list[PurgeImageResp]

    @override
    def as_dict(self) -> dict:
        return asdict(self)
