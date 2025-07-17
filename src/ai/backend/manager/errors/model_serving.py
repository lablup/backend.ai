from aiohttp import web
from ai.backend.common.exception import BackendAIError, ErrorCode, ErrorDetail, ErrorDomain, ErrorOperation


class EndpointNotFound(BackendAIError, web.HTTPNotFound):
    object_name = "endpoint"

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.ENDPOINT,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.NOT_FOUND,
        )


