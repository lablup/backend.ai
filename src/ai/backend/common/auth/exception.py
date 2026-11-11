from typing import override

from aiohttp import web

from ai.backend.common.exception import BackendAIError, ErrorCode, ErrorDetail, ErrorOperation


class InvalidSSHPublicKey(BackendAIError, web.HTTPBadRequest):
    error_type = "https://api.backend.ai/probs/invalid-ssh-public-key"
    error_title = "The SSH public key is invalid or in an unsupported format."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain="user-keypair",
            operation=ErrorOperation.CREATE,
            error_detail=ErrorDetail.INVALID_DATA_FORMAT,
        )
