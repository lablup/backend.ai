from typing import override

from ai.backend.common.clients.storage_backends.hammerspace.exceptions import HammerspaceError
from ai.backend.common.exception import (
    ErrorCode,
    ErrorDetail,
    ErrorDomain,
    ErrorOperation,
)


class ConfigurationError(HammerspaceError):
    error_type = "https://api.backend.ai/probs/hammerspace-invalid-configuration"
    error_title = "Hammerspace configuration is invalid."

    @classmethod
    @override
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.STORAGE,
            operation=ErrorOperation.SETUP,
            error_detail=ErrorDetail.NOT_READY,
        )
