from __future__ import annotations

from typing import override

from aiohttp import web

from ai.backend.common.exception import (
    BackendAIError,
    ErrorCode,
    ErrorDetail,
    ErrorDomain,
    ErrorOperation,
)


class InvalidSocket(BackendAIError, web.HTTPInternalServerError):
    error_type = "https://api.backend.ai/probs/agent/invalid-socket"
    error_title = "Invalid socket."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.AGENT,
            operation=ErrorOperation.GENERIC,
            error_detail=ErrorDetail.INTERNAL_ERROR,
        )


class OutputQueueNotInitializedError(BackendAIError, web.HTTPInternalServerError):
    error_type = "https://api.backend.ai/probs/agent/output-queue-not-initialized"
    error_title = "Output queue is not initialized."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.KERNEL,
            operation=ErrorOperation.EXECUTE,
            error_detail=ErrorDetail.NOT_READY,
        )


class OutputQueueMismatchError(BackendAIError, web.HTTPInternalServerError):
    error_type = "https://api.backend.ai/probs/agent/output-queue-mismatch"
    error_title = "Output queue mismatch."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.KERNEL,
            operation=ErrorOperation.EXECUTE,
            error_detail=ErrorDetail.MISMATCH,
        )


class RunIdNotSetError(BackendAIError, web.HTTPInternalServerError):
    error_type = "https://api.backend.ai/probs/agent/run-id-not-set"
    error_title = "Run ID is not set."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.KERNEL,
            operation=ErrorOperation.EXECUTE,
            error_detail=ErrorDetail.NOT_READY,
        )


class ChannelNotEstablished(BackendAIError, web.HTTPServiceUnavailable):
    error_type = "https://api.backend.ai/probs/kernel-runner/channel-not-established"
    error_title = "The end-to-end kernel channel is not established."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.KERNEL,
            operation=ErrorOperation.ACCESS,
            error_detail=ErrorDetail.UNREACHABLE,
        )


class ChannelIdentityRefused(BackendAIError, web.HTTPForbidden):
    error_type = "https://api.backend.ai/probs/kernel-runner/channel-identity-refused"
    error_title = "The guest presented an identity that was not vouched for."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.KERNEL,
            operation=ErrorOperation.ACCESS,
            error_detail=ErrorDetail.FORBIDDEN,
        )


class StaleAnswerRefused(BackendAIError, web.HTTPConflict):
    error_type = "https://api.backend.ai/probs/kernel-runner/stale-answer-refused"
    error_title = "The kernel answered with an empty or stale reply."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.KERNEL,
            operation=ErrorOperation.EXECUTE,
            error_detail=ErrorDetail.MISMATCH,
        )
