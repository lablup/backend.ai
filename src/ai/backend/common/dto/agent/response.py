from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass
from enum import StrEnum
from typing import Any, Self, TypeVar, override

from pydantic import ConfigDict, Field

from ai.backend.common.dto.internal.health import ConnectivityCheckResponse, HealthStatus
from ai.backend.common.types import BackendAISchema

T = TypeVar("T")


class BaseAgentResponseModel(BackendAISchema):
    """Base class for pydantic response payloads on agent RPC v3 methods.

    Counterpart to ``BaseAgentRequestModel`` on the response side.
    Handlers registered through ``AgentRPCRegistry`` return instances of
    subclasses of this class; the registry dispatcher serialises them via
    ``model_dump(mode="json")`` before handing the payload back to
    callosum.

    Kept separate from ``AbstractAgentResp`` (the dataclass-based v1/v2
    response type) so the two surfaces can evolve independently — v1/v2
    handlers keep emitting ``AbstractAgentResp``; v3 handlers emit
    ``BaseAgentResponseModel`` subclasses.
    """

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        validate_by_name=True,
    )


class HealthResp(BaseAgentResponseModel):
    """Agent RPC v3 response for the ``health_v2`` method.

    Field shape intentionally matches
    ``ai.backend.common.dto.internal.health.HealthResponse`` so manager-
    side code that already understands that type can keep reading the
    same fields. The embedded ``ConnectivityCheckResponse`` is reused
    directly rather than copied, since its schema is owned by the shared
    health DTO module.
    """

    status: HealthStatus = Field(description="Overall agent health status")
    version: str = Field(description="Agent component version")
    component: str = Field(description="Component identifier; always 'agent' in practice")
    connectivity: ConnectivityCheckResponse = Field(
        description="Connectivity check results for external dependencies"
    )


class DeviceHwStatus(StrEnum):
    """Health state for a single compute-plugin device entry."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    OFFLINE = "offline"
    UNAVAILABLE = "unavailable"


class DeviceHardwareInfo(BackendAISchema):
    """Per-device hardware info entry for ``GatherHwinfoResp``.

    The ``metadata`` field is a plugin-defined free-form string map — the
    shape varies per compute plugin (CUDA, ROCm, CPU, mock, …) and is
    deliberately kept open. Converting it to a more structured schema
    would require pinning every plugin to a fixed field set; that is out
    of scope for this RPC surface and belongs in an accelerator-metadata
    refactor instead.
    """

    device_name: str = Field(description="Compute plugin key (e.g., 'cuda', 'rocm', 'cpu')")
    status: DeviceHwStatus
    status_info: str | None = None
    metadata: dict[str, str] = Field(default_factory=dict)


class GatherHwinfoResp(BaseAgentResponseModel):
    """Agent RPC v3 response for the ``gather_hwinfo_v2`` method."""

    devices: list[DeviceHardwareInfo] = Field(
        description="Hardware info collected from every registered compute plugin",
    )


@dataclass
class AbstractAgentResp(ABC):
    @abstractmethod
    def as_dict(self) -> dict[str, Any]:
        raise NotImplementedError


@dataclass
class PurgeImageResp(AbstractAgentResp):
    image: str
    error: str | None = None

    @override
    def as_dict(self) -> dict[str, Any]:
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
    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class PurgeContainersResp(AbstractAgentResp):
    @override
    def as_dict(self) -> dict[str, Any]:
        return {}


@dataclass
class DropKernelRegistryResp(AbstractAgentResp):
    @override
    def as_dict(self) -> dict[str, Any]:
        return {}


@dataclass
class CodeCompletionResult:
    status: str
    error: str | None
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
    def failure(cls, error_msg: str | None = None) -> Self:
        return cls(status="failed", error=error_msg, suggestions=[])

    def as_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "error": self.error,
            "suggestions": self.suggestions,
        }


@dataclass
class CodeCompletionResp(AbstractAgentResp):
    result: CodeCompletionResult

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        return cls(result=CodeCompletionResult.from_dict(data.get("result", {})))

    @classmethod
    def success(cls, completions_data: dict[str, Any]) -> Self:
        return cls(result=CodeCompletionResult.success(completions_data))

    @classmethod
    def failure(cls, error_msg: str) -> Self:
        return cls(result=CodeCompletionResult.failure(error_msg))

    @override
    def as_dict(self) -> dict[str, Any]:
        return {"result": asdict(self.result)}
