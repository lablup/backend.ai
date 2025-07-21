from aiohttp import web

from ai.backend.common.exception import BackendError


class VFolderServiceException(Exception):
    pass


class VFolderNotFound(VFolderServiceException):
    pass


class VFolderCreationFailure(VFolderServiceException):
    pass


class VFolderAlreadyExists(BackendError, web.HTTPConflict):
    pass


class InvalidParameter(VFolderServiceException):
    pass


class InsufficientPrivilege(VFolderServiceException):
    pass


class Forbidden(InvalidParameter):
    pass


class ObjectNotFound(VFolderServiceException):
    pass


class ProjectNotFound(VFolderServiceException):
    pass


class InternalServerError(VFolderServiceException):
    pass


class ModelServiceDependencyNotCleared(VFolderServiceException):
    pass


class TooManyVFoldersFound(VFolderServiceException):
    pass


class VFolderFilterStatusNotAvailable(VFolderServiceException):
    pass


class VFolderFilterStatusFailed(VFolderServiceException):
    pass
