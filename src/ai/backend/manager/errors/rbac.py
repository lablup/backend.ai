from aiohttp import web

from ai.backend.common.exception import (
    BackendAIError,
    ErrorCode,
    ErrorDetail,
    ErrorDomain,
    ErrorOperation,
)


class RBACForbidden(BackendAIError, web.HTTPForbidden):
    error_type = "https://api.backend.ai/probs/rbac-forbidden"
    error_title = "The operation is forbidden due to insufficient RBAC permissions."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.PERMISSION,
            operation=ErrorOperation.ACCESS,
            error_detail=ErrorDetail.FORBIDDEN,
        )
