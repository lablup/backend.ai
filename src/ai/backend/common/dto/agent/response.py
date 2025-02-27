from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass
from typing import Generic, Optional, TypeVar, override


T = TypeVar("T")

@dataclass
class AbstractAgentResponse(ABC, Generic[T]):
    @abstractmethod
    def as_dict(self) -> T:
        raise NotImplementedError

@dataclass
class PurgeImageResponse(AbstractAgentResponse[dict]):
    image: str
    success: bool
    error: Optional[str] = None

    @override
    def as_dict(self) -> dict:
        return asdict(self)


@dataclass
class PurgeImageResponseList(AbstractAgentResponse[list[dict]]):
    responses: list[PurgeImageResponse]

    @override
    def as_dict(self) -> list[dict]:
        return [resp.as_dict() for resp in self.responses]
