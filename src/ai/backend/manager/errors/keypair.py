"""
Keypair-related exceptions.
"""

from __future__ import annotations

from aiohttp import web

from ai.backend.common.exception import (
    BackendAIError,
    ErrorCode,
    ErrorDetail,
    ErrorDomain,
    ErrorOperation,
)


class InvalidSSHPrivateKey(BackendAIError, web.HTTPBadRequest):
    error_type = "https://api.backend.ai/probs/invalid-ssh-private-key"
    error_title = "The SSH private key is invalid or in an unsupported format."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.KEYPAIR,
            operation=ErrorOperation.CREATE,
            error_detail=ErrorDetail.INVALID_DATA_FORMAT,
        )


class InvalidSSHPublicKey(BackendAIError, web.HTTPBadRequest):
    error_type = "https://api.backend.ai/probs/invalid-ssh-public-key"
    error_title = "The SSH public key is invalid or in an unsupported format."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.KEYPAIR,
            operation=ErrorOperation.CREATE,
            error_detail=ErrorDetail.INVALID_DATA_FORMAT,
        )


class SSHKeypairMismatch(BackendAIError, web.HTTPBadRequest):
    error_type = "https://api.backend.ai/probs/ssh-keypair-mismatch"
    error_title = "The SSH public key does not match the private key."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.KEYPAIR,
            operation=ErrorOperation.CREATE,
            error_detail=ErrorDetail.INVALID_PARAMETERS,
        )
