from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass
from typing import Any, Optional, Self, TypeVar, override

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


@dataclass
class PurgeContainersResp(AbstractAgentResp):
    @override
    def as_dict(self) -> dict:
        return {}


@dataclass
class DropKernelRegistryResp(AbstractAgentResp):
    @override
    def as_dict(self) -> dict:
        return {}


@dataclass
class CodeCompletionResult:
    status: str
    error: Optional[str]
    suggestions: list[str]

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        # NOTE: tuple to list conversion code is written because callosum serialize all array inputs to tuples
        suggestions = data.get("suggestions", [])
        if isinstance(suggestions, tuple):
            suggestions = list(suggestions)
        return cls(
            status=data.get("status", "finished"),
            error=data.get("error"),
            suggestions=suggestions,
        )

    @classmethod
    def success(cls, suggestion_result: dict[str, list[str]]) -> Self:
        return cls(
            status="finished", error=None, suggestions=suggestion_result.get("suggestions", [])
        )

    @classmethod
    def failure(cls, error_msg: Optional[str] = None) -> Self:
        return cls(status="failed", error=error_msg, suggestions=[])

    def as_dict(self) -> dict:
        return {
            "status": self.status,
            "error": self.error,
            "suggestions": self.suggestions,
        }


@dataclass
class CodeCompletionResp(AbstractAgentResp):
    result: CodeCompletionResult

    @classmethod
    def from_dict(cls, data: dict) -> Self:
        return cls(result=CodeCompletionResult.from_dict(data.get("result", {})))

    @classmethod
    def success(cls, completions_data: dict) -> Self:
        return cls(result=CodeCompletionResult.success(completions_data))

    @classmethod
    def failure(cls, error_msg: str) -> Self:
        return cls(result=CodeCompletionResult.failure(error_msg))

    @override
    def as_dict(self) -> dict:
        return {"result": asdict(self.result)}
