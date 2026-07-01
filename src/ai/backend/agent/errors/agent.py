"""
Agent operation-related exceptions.
"""

from __future__ import annotations

from typing import Any

from aiohttp import web

from ai.backend.common.exception import (
    BackendAIError,
    ErrorCode,
    ErrorDetail,
    ErrorDomain,
    ErrorOperation,
)


class ImageArchitectureMismatchError(BackendAIError, web.HTTPBadRequest):
    """Raised when image architecture does not match the agent's architecture."""

    error_type = "https://api.backend.ai/probs/agent/image-architecture-mismatch"
    error_title = "Image architecture mismatch."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.IMAGE,
            operation=ErrorOperation.ACCESS,
            error_detail=ErrorDetail.MISMATCH,
        )


class ImagePullTimeoutError(BackendAIError, web.HTTPGatewayTimeout):
    """Raised when image pull times out."""

    error_type = "https://api.backend.ai/probs/agent/image-pull-timeout"
    error_title = "Image pull timeout."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.IMAGE,
            operation=ErrorOperation.ACCESS,
            error_detail=ErrorDetail.TIMEOUT,
        )


class ContainerCreationFailedError(BackendAIError, web.HTTPInternalServerError):
    """Raised when container creation fails (final error to return to client)."""

    error_type = "https://api.backend.ai/probs/agent/container-creation-failed"
    error_title = "Container creation failed."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.KERNEL,
            operation=ErrorOperation.CREATE,
            error_detail=ErrorDetail.UNAVAILABLE,
        )


class ContainerStartupTimeoutError(BackendAIError, web.HTTPGatewayTimeout):
    """Raised when container startup times out."""

    error_type = "https://api.backend.ai/probs/agent/container-startup-timeout"
    error_title = "Container startup timeout."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.KERNEL,
            operation=ErrorOperation.START,
            error_detail=ErrorDetail.TIMEOUT,
        )


class ContainerStartupCancelledError(BackendAIError, web.HTTPInternalServerError):
    """Raised when container startup is cancelled."""

    error_type = "https://api.backend.ai/probs/agent/container-startup-cancelled"
    error_title = "Container startup cancelled."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.KERNEL,
            operation=ErrorOperation.START,
            error_detail=ErrorDetail.CANCELED,
        )


class ContainerStartupFailedError(BackendAIError, web.HTTPInternalServerError):
    """Raised when container startup fails."""

    error_type = "https://api.backend.ai/probs/agent/container-startup-failed"
    error_title = "Container startup failed."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.KERNEL,
            operation=ErrorOperation.START,
            error_detail=ErrorDetail.NOT_READY,
        )


class ReservedPortError(BackendAIError, web.HTTPBadRequest):
    """Raised when attempting to use reserved ports."""

    error_type = "https://api.backend.ai/probs/agent/reserved-port"
    error_title = "Reserved port cannot be used."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.KERNEL,
            operation=ErrorOperation.CREATE,
            error_detail=ErrorDetail.CONFLICT,
        )


class PortConflictError(BackendAIError, web.HTTPBadRequest):
    """Raised when a port conflicts with existing services."""

    error_type = "https://api.backend.ai/probs/agent/port-conflict"
    error_title = "Port conflicts with existing service."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.KERNEL,
            operation=ErrorOperation.CREATE,
            error_detail=ErrorDetail.CONFLICT,
        )


class ModelDefinitionNotFoundError(BackendAIError, web.HTTPBadRequest):
    """Raised when model definition file is not found."""

    error_type = "https://api.backend.ai/probs/agent/model-definition-not-found"
    error_title = "Model definition file not found."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.MODEL_SERVICE,
            operation=ErrorOperation.ACCESS,
            error_detail=ErrorDetail.NOT_FOUND,
        )


class ModelDefinitionEmptyError(BackendAIError, web.HTTPBadRequest):
    """Raised when model definition is empty."""

    error_type = "https://api.backend.ai/probs/agent/model-definition-empty"
    error_title = "Model definition is empty."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.MODEL_SERVICE,
            operation=ErrorOperation.ACCESS,
            error_detail=ErrorDetail.INVALID_PARAMETERS,
        )


class ModelDefinitionInvalidYAMLError(BackendAIError, web.HTTPBadRequest):
    """Raised when model definition YAML syntax is invalid."""

    error_type = "https://api.backend.ai/probs/agent/model-definition-invalid-yaml"
    error_title = "Invalid YAML syntax in model definition."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.MODEL_SERVICE,
            operation=ErrorOperation.PARSING,
            error_detail=ErrorDetail.INVALID_DATA_FORMAT,
        )


class ModelFolderNotSpecifiedError(BackendAIError, web.HTTPBadRequest):
    """Raised when no model virtual folder is specified."""

    error_type = "https://api.backend.ai/probs/agent/model-folder-not-specified"
    error_title = "Model folder not specified."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.MODEL_SERVICE,
            operation=ErrorOperation.CREATE,
            error_detail=ErrorDetail.INVALID_PARAMETERS,
        )


class ImageCommandRequiredError(BackendAIError, web.HTTPBadRequest):
    """Raised when image command is required but not found."""

    error_type = "https://api.backend.ai/probs/agent/image-command-required"
    error_title = "Image command is required."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.IMAGE,
            operation=ErrorOperation.ACCESS,
            error_detail=ErrorDetail.INVALID_PARAMETERS,
        )


class AgentInitializationError(BackendAIError, web.HTTPInternalServerError):
    """Raised when agent initialization fails."""

    error_type = "https://api.backend.ai/probs/agent/initialization-failed"
    error_title = "Agent initialization failed."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.AGENT,
            operation=ErrorOperation.SETUP,
            error_detail=ErrorDetail.NOT_READY,
        )


class InvalidAgentConfigError(BackendAIError, web.HTTPBadRequest):
    """Raised when agent configuration is invalid."""

    error_type = "https://api.backend.ai/probs/agent/invalid-config"
    error_title = "Invalid agent configuration."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.AGENT,
            operation=ErrorOperation.SETUP,
            error_detail=ErrorDetail.INVALID_PARAMETERS,
        )


class InvalidMountPathError(BackendAIError, web.HTTPBadRequest):
    """Raised when mount path configuration is invalid."""

    error_type = "https://api.backend.ai/probs/agent/invalid-mount-path"
    error_title = "Invalid mount path."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.AGENT,
            operation=ErrorOperation.SETUP,
            error_detail=ErrorDetail.INVALID_PARAMETERS,
        )


class InvalidLoggingConfigError(BackendAIError, web.HTTPBadRequest):
    """Raised when logging configuration is invalid."""

    error_type = "https://api.backend.ai/probs/agent/invalid-logging-config"
    error_title = "Invalid logging configuration."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.AGENT,
            operation=ErrorOperation.SETUP,
            error_detail=ErrorDetail.INVALID_PARAMETERS,
        )


class InvalidChunkSizeError(BackendAIError, web.HTTPBadRequest):
    """Raised when chunk size is invalid."""

    error_type = "https://api.backend.ai/probs/agent/invalid-chunk-size"
    error_title = "Invalid chunk size."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.KERNEL,
            operation=ErrorOperation.EXECUTE,
            error_detail=ErrorDetail.INVALID_PARAMETERS,
        )


class AsyncioTaskNotAvailableError(BackendAIError, web.HTTPInternalServerError):
    """Raised when the current asyncio task context is not available."""

    error_type = "https://api.backend.ai/probs/agent/asyncio-task-not-available"
    error_title = "Asyncio task context not available."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.KERNEL,
            operation=ErrorOperation.EXECUTE,
            error_detail=ErrorDetail.NOT_READY,
        )


class KernelNotFoundError(BackendAIError, web.HTTPNotFound):
    """Raised when a kernel is not found."""

    error_type = "https://api.backend.ai/probs/agent/kernel-not-found"
    error_title = "Kernel not found."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.KERNEL,
            operation=ErrorOperation.ACCESS,
            error_detail=ErrorDetail.NOT_FOUND,
        )


class InitializationError(BackendAIError, web.HTTPInternalServerError):
    """Raised during agent initialization and compute plugin setup."""

    error_type = "https://api.backend.ai/probs/agent/initialization-error"
    error_title = "Agent initialization error."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.AGENT,
            operation=ErrorOperation.SETUP,
            error_detail=ErrorDetail.INTERNAL_ERROR,
        )


class InvalidArgumentError(BackendAIError, web.HTTPBadRequest):
    """Raised when an invalid argument is given to an agent operation."""

    error_type = "https://api.backend.ai/probs/agent/invalid-argument"
    error_title = "Invalid argument."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.AGENT,
            operation=ErrorOperation.GENERIC,
            error_detail=ErrorDetail.INVALID_PARAMETERS,
        )


class UnsupportedBaseDistroError(BackendAIError, web.HTTPBadRequest):
    """Raised when the base distribution of an image cannot be determined or supported."""

    error_type = "https://api.backend.ai/probs/agent/unsupported-base-distro"
    error_title = "Unsupported base distribution."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.IMAGE,
            operation=ErrorOperation.ACCESS,
            error_detail=ErrorDetail.NOT_IMPLEMENTED,
        )


class ContainerCreationError(BackendAIError, web.HTTPInternalServerError):
    """Raised when the underlying container runtime fails to create a container."""

    error_type = "https://api.backend.ai/probs/agent/container-creation-error"
    error_title = "Container creation error."

    def __init__(
        self, container_id: str, message: str | None = None, *args: Any, **kwargs: Any
    ) -> None:
        self.container_id = container_id
        self.message = message
        super().__init__(extra_msg=message)

    def __reduce__(self) -> tuple[type[BackendAIError], tuple[Any, ...], dict[str, Any]]:
        return (self.__class__, (self.container_id, self.message), self.__dict__)

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.KERNEL,
            operation=ErrorOperation.CREATE,
            error_detail=ErrorDetail.INTERNAL_ERROR,
        )


class K8sError(BackendAIError, web.HTTPInternalServerError):
    """Raised when a Kubernetes operation fails."""

    error_type = "https://api.backend.ai/probs/agent/k8s-error"
    error_title = "Kubernetes error."

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(extra_msg=message)

    def __reduce__(self) -> tuple[type[BackendAIError], tuple[Any, ...], dict[str, Any]]:
        return (self.__class__, (self.message,), self.__dict__)

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.AGENT,
            operation=ErrorOperation.GENERIC,
            error_detail=ErrorDetail.INTERNAL_ERROR,
        )


class NetworkPluginNotFound(BackendAIError, web.HTTPInternalServerError):
    """Raised when a configured network plugin cannot be found."""

    error_type = "https://api.backend.ai/probs/agent/network-plugin-not-found"
    error_title = "Network plugin not found."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.AGENT,
            operation=ErrorOperation.SETUP,
            error_detail=ErrorDetail.NOT_FOUND,
        )


class ServicePortAlreadyUsedError(BackendAIError, web.HTTPConflict):
    """Raised when a port is already used by another service."""

    error_type = "https://api.backend.ai/probs/agent/service-port-already-used"
    error_title = "Service port already used."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.KERNEL,
            operation=ErrorOperation.CREATE,
            error_detail=ErrorDetail.CONFLICT,
        )


class InvalidSocket(BackendAIError, web.HTTPInternalServerError):
    """Raised when an invalid socket is encountered."""

    error_type = "https://api.backend.ai/probs/agent/invalid-socket"
    error_title = "Invalid socket."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.AGENT,
            operation=ErrorOperation.GENERIC,
            error_detail=ErrorDetail.INTERNAL_ERROR,
        )
