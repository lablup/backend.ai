from typing import override

from aiohttp import web

from ai.backend.common.clients.storage_backends.gpfs.exceptions import GPFSError
from ai.backend.common.exception import (
    ErrorCode,
    ErrorDetail,
    ErrorDomain,
    ErrorOperation,
)


class GPFSNoMetricError(GPFSError, web.HTTPInternalServerError):
    error_type = "https://api.backend.ai/probs/gpfs-no-metric"
    error_title = "GPFS metric not available."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(ErrorDomain.STORAGE, ErrorOperation.READ, ErrorDetail.NOT_FOUND)
