"""
Resource-related exceptions for the agent.
"""

from __future__ import annotations

from collections.abc import Sequence
from decimal import Decimal
from typing import Any

from aiohttp import web

from ai.backend.common.exception import (
    BackendAIError,
    ErrorCode,
    ErrorDetail,
    ErrorDomain,
    ErrorOperation,
)
from ai.backend.common.types import DeviceId, SlotName


class ResourceError(BackendAIError, web.HTTPBadRequest):
    """Base class for agent resource allocation errors."""

    error_type = "https://api.backend.ai/probs/agent/resource-error"
    error_title = "Resource error."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.AGENT,
            operation=ErrorOperation.CREATE,
            error_detail=ErrorDetail.INVALID_PARAMETERS,
        )


class UnsupportedResource(ResourceError):
    """Raised when a requested resource slot is not supported."""

    error_type = "https://api.backend.ai/probs/agent/unsupported-resource"
    error_title = "Unsupported resource."


class InvalidResourceCombination(ResourceError):
    """Raised when the combination of requested resources is invalid."""

    error_type = "https://api.backend.ai/probs/agent/invalid-resource-combination"
    error_title = "Invalid resource combination."


class InvalidResourceArgument(ResourceError):
    """Raised when a resource argument is invalid."""

    error_type = "https://api.backend.ai/probs/agent/invalid-resource-argument"
    error_title = "Invalid resource argument."


class NotMultipleOfQuantum(InvalidResourceArgument):
    """Raised when a requested amount is not a multiple of the slot quantum."""

    error_type = "https://api.backend.ai/probs/agent/not-multiple-of-quantum"
    error_title = "Resource amount is not a multiple of the quantum."


class InsufficientResource(ResourceError):
    """Raised when the allocatable amount is insufficient for the request."""

    error_type = "https://api.backend.ai/probs/agent/insufficient-resource"
    error_title = "Insufficient resource."

    def __init__(
        self,
        msg: str,
        slot_name: SlotName,
        requested_alloc: Decimal,
        total_allocatable: Decimal | int,
        allocation: dict[SlotName, dict[DeviceId, Decimal]],
        context_tag: str | None = None,
    ) -> None:
        self.msg = msg
        self.slot_name = slot_name
        self.requested_alloc = requested_alloc
        self.total_allocatable = total_allocatable
        self.allocation = allocation
        self.context_tag = context_tag
        super().__init__(extra_msg=str(self))

    def __str__(self) -> str:
        return (
            f"InsufficientResource: {self.msg} ({self.slot_name}"
            + (f" (tag: {self.context_tag!r}), " if self.context_tag else ", ")
            + f"allocating {self.requested_alloc} out of {self.total_allocatable})"
        )

    def __reduce__(self) -> tuple[type[BackendAIError], tuple[Any, ...], dict[str, Any]]:
        return (
            self.__class__,
            (
                self.msg,
                self.slot_name,
                self.requested_alloc,
                self.total_allocatable,
                self.allocation,
                self.context_tag,
            ),
            self.__dict__,
        )


class FractionalResourceFragmented(ResourceError):
    """Raised when fractional resources are too fragmented to allocate."""

    error_type = "https://api.backend.ai/probs/agent/fractional-resource-fragmented"
    error_title = "Fractional resource fragmented."

    def __init__(
        self,
        msg: str,
        slot_name: SlotName,
        requested_alloc: Decimal,
        dev_allocs: Sequence[tuple[DeviceId, Decimal]],
        context_tag: str | None = None,
    ) -> None:
        self.msg = msg
        self.slot_name = slot_name
        self.requested_alloc = requested_alloc
        self.dev_allocs = dev_allocs
        self.context_tag = context_tag
        super().__init__(extra_msg=str(self))

    def __str__(self) -> str:
        return (
            f"FractionalResourceFragmented: {self.msg} ({self.slot_name}"
            + (f" (tag: {self.context_tag!r}), " if self.context_tag else ", ")
            + f"allocating {self.requested_alloc} from {self.dev_allocs})"
        )

    def __reduce__(self) -> tuple[type[BackendAIError], tuple[Any, ...], dict[str, Any]]:
        return (
            self.__class__,
            (
                self.msg,
                self.slot_name,
                self.requested_alloc,
                self.dev_allocs,
                self.context_tag,
            ),
            self.__dict__,
        )


class InvalidResourceConfigError(BackendAIError, web.HTTPBadRequest):
    """Raised when resource configuration is invalid."""

    error_type = "https://api.backend.ai/probs/agent/invalid-resource-config"
    error_title = "Invalid resource configuration."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.AGENT,
            operation=ErrorOperation.SETUP,
            error_detail=ErrorDetail.INVALID_PARAMETERS,
        )


class AgentIdNotFoundError(BackendAIError, web.HTTPNotFound):
    """Raised when the agent ID is not found in the configuration."""

    error_type = "https://api.backend.ai/probs/agent/agent-id-not-found"
    error_title = "Agent ID not found."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.AGENT,
            operation=ErrorOperation.ACCESS,
            error_detail=ErrorDetail.NOT_FOUND,
        )


class ResourceOverAllocatedError(BackendAIError, web.HTTPBadRequest):
    """Raised when resources are over-allocated beyond their limit."""

    error_type = "https://api.backend.ai/probs/agent/resource-over-allocated"
    error_title = "Resources are over-allocated."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.AGENT,
            operation=ErrorOperation.CHECK_LIMIT,
            error_detail=ErrorDetail.INVALID_PARAMETERS,
        )


class ResourceAllocationError(BackendAIError, web.HTTPInternalServerError):
    """Raised when resource allocation fails due to internal error."""

    error_type = "https://api.backend.ai/probs/agent/resource-allocation-error"
    error_title = "Resource allocation error."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.AGENT,
            operation=ErrorOperation.CREATE,
            error_detail=ErrorDetail.MISMATCH,
        )


class InvalidOvercommitFactorError(BackendAIError, web.HTTPBadRequest):
    """Raised when overcommit factor is out of valid range."""

    error_type = "https://api.backend.ai/probs/agent/invalid-overcommit-factor"
    error_title = "Invalid overcommit factor."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.AGENT,
            operation=ErrorOperation.SETUP,
            error_detail=ErrorDetail.INVALID_PARAMETERS,
        )


class InvalidAllocMapTypeError(BackendAIError, web.HTTPInternalServerError):
    """Raised when allocation map type is invalid."""

    error_type = "https://api.backend.ai/probs/agent/invalid-alloc-map-type"
    error_title = "Invalid allocation map type."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.AGENT,
            operation=ErrorOperation.ACCESS,
            error_detail=ErrorDetail.MISMATCH,
        )


class InvalidMeasurementError(BackendAIError, web.HTTPInternalServerError):
    """Raised when measurement data is invalid."""

    error_type = "https://api.backend.ai/probs/agent/invalid-measurement"
    error_title = "Invalid measurement data."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.AGENT,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.MISMATCH,
        )


class InvalidConfigFormatError(BackendAIError, web.HTTPBadRequest):
    """Raised when configuration format is invalid."""

    error_type = "https://api.backend.ai/probs/agent/invalid-config-format"
    error_title = "Invalid configuration format."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.AGENT,
            operation=ErrorOperation.SETUP,
            error_detail=ErrorDetail.INVALID_DATA_FORMAT,
        )


class InvalidContainerMeasurementError(BackendAIError, web.HTTPInternalServerError):
    """Raised when container measurement type is invalid."""

    error_type = "https://api.backend.ai/probs/agent/invalid-container-measurement"
    error_title = "Invalid container measurement type."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.AGENT,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.INVALID_DATA_FORMAT,
        )


class PortPoolExhaustedError(BackendAIError, web.HTTPServiceUnavailable):
    """Raised when no host ports are available for allocation.

    This covers two cases: the pool is fully empty, or every remaining
    port is still within its post-release cooldown window.
    """

    error_type = "https://api.backend.ai/probs/agent/port-pool-exhausted"
    error_title = "Host port pool exhausted."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.AGENT,
            operation=ErrorOperation.CREATE,
            error_detail=ErrorDetail.UNAVAILABLE,
        )
