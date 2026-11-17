from aiohttp import web

<<<<<<< HEAD
=======
from aiohttp import web

from ai.backend.common.clients.storage_backends.hammerspace.exceptions import HammerspaceError
>>>>>>> d2ebe76c5 (fix(BA-9049): give the error classes of the agent, common, manager and storage packages an HTTP status (#17132))
from ai.backend.common.exception import (
    BackendAIError,
    ErrorCode,
    ErrorDetail,
    ErrorDomain,
    ErrorOperation,
)


<<<<<<< HEAD
class HammerspaceError(BackendAIError):
    """Base error for Hammerspace-related errors."""


class ConfigurationError(HammerspaceError):
=======
class ConfigurationError(HammerspaceError, web.HTTPInternalServerError):
>>>>>>> d2ebe76c5 (fix(BA-9049): give the error classes of the agent, common, manager and storage packages an HTTP status (#17132))
    error_type = "https://api.backend.ai/probs/hammerspace-invalid-configuration"
    error_title = "Hammerspace configuration is invalid."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.STORAGE,
            operation=ErrorOperation.SETUP,
            error_detail=ErrorDetail.NOT_READY,
        )


class AuthenticationError(HammerspaceError, web.HTTPUnauthorized):
    error_type = "https://api.backend.ai/probs/hammerspace-authentication-failure"
    error_title = "Hammerspace API authentication failed."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.STORAGE,
            operation=ErrorOperation.AUTH,
            error_detail=ErrorDetail.UNAUTHORIZED,
        )


class ObjectiveNotFound(HammerspaceError, web.HTTPNotFound):
    error_type = "https://api.backend.ai/probs/hammerspace-objective-not-found"
    error_title = "Hammerspace has no such objective."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.STORAGE,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.NOT_FOUND,
        )


class ShareNotFound(HammerspaceError, web.HTTPNotFound):
    error_type = "https://api.backend.ai/probs/hammerspace-share-not-found"
    error_title = "Hammerspace has no such share."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.STORAGE,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.NOT_FOUND,
        )


class VolumeNotFound(HammerspaceError, web.HTTPNotFound):
    error_type = "https://api.backend.ai/probs/hammerspace-volume-not-found"
    error_title = "Hammerspace has no such volume."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.STORAGE,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.NOT_FOUND,
        )
