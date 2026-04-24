from aiohttp import web

from ai.backend.common.exception import (
    BackendAIError,
    ErrorCode,
    ErrorDetail,
    ErrorDomain,
    ErrorOperation,
)


class AppConfigPolicyConflict(BackendAIError, web.HTTPConflict):
    error_type = "https://api.backend.ai/probs/app-config-policy-conflict"
    error_title = "An app-config policy with the same config_name already exists."

    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.BACKENDAI,
            operation=ErrorOperation.CREATE,
            error_detail=ErrorDetail.CONFLICT,
        )
