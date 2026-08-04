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


class BrokerUnreachable(BackendAIError, web.HTTPServiceUnavailable):
    error_type = "https://api.backend.ai/probs/confidential-broker-unreachable"
    error_title = "The key broker is unreachable; the request is queued."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.EXTERNAL_SYSTEM,
            operation=ErrorOperation.REQUEST,
            error_detail=ErrorDetail.UNAVAILABLE,
        )


class ReleaseDenied(BackendAIError, web.HTTPForbidden):
    error_type = "https://api.backend.ai/probs/confidential-release-denied"
    error_title = "The key broker refused to release the requested resource."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.EXTERNAL_SYSTEM,
            operation=ErrorOperation.GRANT,
            error_detail=ErrorDetail.FORBIDDEN,
        )


class BrokerRejected(BackendAIError, web.HTTPBadRequest):
    error_type = "https://api.backend.ai/probs/confidential-broker-rejected"
    error_title = "The key broker rejected an administrative submission."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.EXTERNAL_SYSTEM,
            operation=ErrorOperation.REQUEST,
            error_detail=ErrorDetail.BAD_REQUEST,
        )


class ShimRefusal(BackendAIError, web.HTTPForbidden):
    error_type = "https://api.backend.ai/probs/confidential-shim-refusal"
    error_title = "The authorisation shim refused a request outside the manager's two capabilities."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.EXTERNAL_SYSTEM,
            operation=ErrorOperation.ACCESS,
            error_detail=ErrorDetail.FORBIDDEN,
        )


class NonceQuotaExhausted(BackendAIError, web.HTTPForbidden):
    error_type = "https://api.backend.ai/probs/confidential-nonce-quota-exhausted"
    error_title = "The session's launch-nonce claim quota is exhausted."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.SESSION,
            operation=ErrorOperation.ACCESS,
            error_detail=ErrorDetail.FORBIDDEN,
        )


class ReferenceValueRejected(BackendAIError, web.HTTPForbidden):
    error_type = "https://api.backend.ai/probs/confidential-reference-value-rejected"
    error_title = "Reference-value registration failed the attested-identity and pipeline-signature gate."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.IMAGE,
            operation=ErrorOperation.CREATE,
            error_detail=ErrorDetail.FORBIDDEN,
        )


class ConfidentialCapabilityRefused(BackendAIError, web.HTTPBadRequest):
    error_type = "https://api.backend.ai/probs/confidential-capability-refused"
    error_title = "The scaling group cannot be marked confidential-capable."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.SCALING_GROUP,
            operation=ErrorOperation.UPDATE,
            error_detail=ErrorDetail.INVALID_PARAMETERS,
        )


class MeasuredBlobNotFound(BackendAIError, web.HTTPNotFound):
    error_type = "https://api.backend.ai/probs/confidential-measured-blob-not-found"
    error_title = "No measured configuration blob is registered for this image digest and profile."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.IMAGE,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.NOT_FOUND,
        )


class AdmissionBeltExceeded(BackendAIError, web.HTTPConflict):
    error_type = "https://api.backend.ai/probs/confidential-admission-belt-exceeded"
    error_title = "The interim per-image-and-profile admission limit is already met."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.SESSION,
            operation=ErrorOperation.CHECK_LIMIT,
            error_detail=ErrorDetail.CONFLICT,
        )


class FolderEscrowUnreachable(BackendAIError, web.HTTPServiceUnavailable):
    error_type = "https://api.backend.ai/probs/confidential-folder-escrow-unreachable"
    error_title = (
        "The durable folder-key escrow is unreachable, so no folder key may be minted:"
        " a key that lives only in the broker and nowhere else is unrecoverable if the"
        " broker's disk is lost."
    )

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.VFOLDER,
            operation=ErrorOperation.CREATE,
            error_detail=ErrorDetail.UNAVAILABLE,
        )


class FolderEncryptionMissing(BackendAIError, web.HTTPBadRequest):
    error_type = "https://api.backend.ai/probs/confidential-folder-encryption-missing"
    error_title = (
        "A folder reached a confidential session without an encryption descriptor;"
        " mounting it would put plaintext on storage the operator can read."
    )

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.VFOLDER,
            operation=ErrorOperation.SETUP,
            error_detail=ErrorDetail.INVALID_PARAMETERS,
        )


class ClientFormatRefused(BackendAIError, web.HTTPPreconditionFailed):
    error_type = "https://api.backend.ai/probs/confidential-client-format-refused"
    error_title = "The client does not speak the confidential storage format this folder requires."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.VFOLDER,
            operation=ErrorOperation.ACCESS,
            error_detail=ErrorDetail.INVALID_PARAMETERS,
        )


class ImmutableEncryptionTier(BackendAIError, web.HTTPConflict):
    error_type = "https://api.backend.ai/probs/confidential-immutable-encryption-tier"
    error_title = "A folder's encryption tier is fixed at creation and cannot be changed."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.VFOLDER,
            operation=ErrorOperation.UPDATE,
            error_detail=ErrorDetail.CONFLICT,
        )
