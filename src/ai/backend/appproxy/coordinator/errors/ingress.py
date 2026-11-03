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


class ApiDeliveryWorkerUnreachableError(BackendAIError, web.HTTPBadGateway):
    """Raised when an api-delivery worker cannot be reached."""

    error_type = "https://api.backend.ai/probs/appproxy-coordinator/api-delivery-worker-unreachable"
    error_title = "An api-delivery worker cannot be reached."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.APPPROXY,
            operation=ErrorOperation.REQUEST,
            error_detail=ErrorDetail.UNREACHABLE,
        )


class ApiDeliveryWorkerRejectedError(BackendAIError, web.HTTPBadRequest):
    """Raised when an api-delivery worker answers a request with a 4xx."""

    error_type = "https://api.backend.ai/probs/appproxy-coordinator/api-delivery-worker-rejected"
    error_title = "An api-delivery worker rejected the request."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.APPPROXY,
            operation=ErrorOperation.REQUEST,
            error_detail=ErrorDetail.BAD_REQUEST,
        )


class ApiDeliveryWorkerServerError(BackendAIError, web.HTTPBadGateway):
    """Raised when an api-delivery worker answers a request with a 5xx."""

    error_type = (
        "https://api.backend.ai/probs/appproxy-coordinator/api-delivery-worker-server-error"
    )
    error_title = "An api-delivery worker failed to handle the request."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.APPPROXY,
            operation=ErrorOperation.REQUEST,
            error_detail=ErrorDetail.INTERNAL_ERROR,
        )


class IngressPushFailedError(BackendAIError, web.HTTPBadGateway):
    """Raised after every push has settled when any push to a worker or to Traefik etcd failed."""

    error_type = "https://api.backend.ai/probs/appproxy-coordinator/ingress-push-failed"
    error_title = "Ingress pushes failed."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.APPPROXY,
            operation=ErrorOperation.REQUEST,
            error_detail=ErrorDetail.UNAVAILABLE,
        )


class TraefikIngressConcurrentWriteError(BackendAIError, web.HTTPConflict):
    """Raised when another write to the same frontend commits between the revision check and
    this upsert's write. Resending the ingress applies it or reports a newer revision."""

    error_type = (
        "https://api.backend.ai/probs/appproxy-coordinator/traefik-ingress-concurrent-write"
    )
    error_title = "Another write to the ingress frontend committed first."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.APPPROXY,
            operation=ErrorOperation.UPSERT,
            error_detail=ErrorDetail.CONFLICT,
        )


class TraefikIngressRevisionConflictError(BackendAIError, web.HTTPConflict):
    """Raised when an upsert carries a revision older than the one Traefik etcd holds."""

    error_type = (
        "https://api.backend.ai/probs/appproxy-coordinator/traefik-ingress-revision-conflict"
    )
    error_title = "Ingress revision is older than the one Traefik etcd holds."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.APPPROXY,
            operation=ErrorOperation.UPSERT,
            error_detail=ErrorDetail.CONFLICT,
        )


class TraefikWildcardDomainMissingError(BackendAIError, web.HTTPInternalServerError):
    """Raised when a wildcard ingress targets a worker registered without a wildcard domain."""

    error_type = "https://api.backend.ai/probs/appproxy-coordinator/traefik-wildcard-domain-missing"
    error_title = "The worker has no wildcard domain to route a wildcard ingress."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.APPPROXY,
            operation=ErrorOperation.UPSERT,
            error_detail=ErrorDetail.INTERNAL_ERROR,
        )


class TraefikIngressWriteFailedError(BackendAIError, web.HTTPBadGateway):
    """Raised after every ingress write to Traefik etcd has settled when any of them failed."""

    error_type = "https://api.backend.ai/probs/appproxy-coordinator/traefik-ingress-write-failed"
    error_title = "Ingress writes to Traefik etcd failed."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.APPPROXY,
            operation=ErrorOperation.REQUEST,
            error_detail=ErrorDetail.UNAVAILABLE,
        )


class TraefikEtcdRequestFailedError(BackendAIError, web.HTTPBadGateway):
    """Raised when a request to Traefik etcd fails."""

    error_type = "https://api.backend.ai/probs/appproxy-coordinator/traefik-etcd-request-failed"
    error_title = "A request to Traefik etcd failed."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.APPPROXY,
            operation=ErrorOperation.REQUEST,
            error_detail=ErrorDetail.UNAVAILABLE,
        )


class TraefikAppliedIngressRevisionInvalidError(BackendAIError, web.HTTPInternalServerError):
    """Raised when an applied ingress revision read from Traefik etcd does not parse."""

    error_type = (
        "https://api.backend.ai/probs/appproxy-coordinator/traefik-applied-ingress-revision-invalid"
    )
    error_title = "Ingress revision applied in Traefik etcd is invalid."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.APPPROXY,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.INVALID_DATA_FORMAT,
        )
