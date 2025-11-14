import enum
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Mapping, Optional, Self

from aiohttp import web

from .json import dump_json


class ConfigurationError(Exception):
    invalid_data: Mapping[str, Any]

    def __init__(self, invalid_data: Mapping[str, Any]) -> None:
        super().__init__(invalid_data)
        self.invalid_data = invalid_data


class InvalidAPIHandlerDefinition(Exception):
    pass


class UnknownImageReference(ValueError):
    """
    Represents an error for invalid/unknown image reference.
    The first argument of this exception should be the reference given by the user.
    """

    def __str__(self) -> str:
        return f"Unknown image reference: {self.args[0]}"


class ImageNotAvailable(ValueError):
    """
    Represents an error for unavailability of the image in agents.
    The first argument of this exception should be the reference given by the user.
    """

    def __str__(self) -> str:
        return f"Unavailable image in the agent: {self.args[0]}"


class UnknownImageRegistry(ValueError):
    """
    Represents an error for invalid/unknown image registry.
    The first argument of this exception should be the registry given by the user.
    """

    def __str__(self) -> str:
        return f"Unknown image registry: {self.args[0]}"


class InvalidImageName(ValueError):
    """
    Represents an invalid string for image name.
    """

    def __str__(self) -> str:
        return f"Invalid image name: {self.args[0]}"


class InvalidImageTag(ValueError):
    """
    Represents an invalid string for image tag and full image name.
    Image tag should be a string of form below

    ```
    <version-stringA>-<platform-tag-1A>-<platform-tag-2A>-....
    ```
    """

    def __init__(self, tag: str, full_name: str | None = None) -> None:
        super().__init__(tag, full_name)
        self._tag = tag
        self._full_name = full_name

    def __str__(self) -> str:
        if self._full_name is not None:
            return f"Invalid or duplicate image name tag: {self._tag}, full image name: {self._full_name}"
        else:
            return f"Invalid or duplicate image name tag: {self._tag}"


class ProjectMismatchWithCanonical(ValueError):
    """
    Represent the project value does not match the canonical value when parsing the string representing the image in ImageRef.
    """

    def __init__(self, project: str, canonical: str) -> None:
        super().__init__(project, canonical)
        self._project = project
        self._canonical = canonical

    def __str__(self) -> str:
        return f'Project "{self._project}" mismatch with the image canonical: {self._canonical}'


class AliasResolutionFailed(ValueError):
    """
    Represents an alias resolution failure.
    The first argument of this exception should be the alias given by the user.
    """

    def __str__(self) -> str:
        return f"Failed to resolve alias: {self.args[0]}"


class InvalidIpAddressValue(ValueError):
    """
    Represents an invalid value for ip_address.
    """


class VolumeMountFailed(RuntimeError):
    """
    Represents a mount process failure.
    """


class VolumeUnmountFailed(RuntimeError):
    """
    Represents a umount process failure.
    """


class ErrorDomain(enum.StrEnum):
    """
    An enum to represent the domain of the error.
    The domain is a string that represents the area where the error occurred.
    """

    BACKENDAI = "backendai"  # Whenever possible, use specific domain names instead of this one.
    API = "api"
    ARTIFACT = "artifact"
    ARTIFACT_REGISTRY = "artifact-registry"
    ARTIFACT_REVISION = "artifact-revision"
    ARTIFACT_ASSOCIATION = "artifact-association"
    OBJECT_STORAGE = "object-storage"
    STORAGE_NAMESPACE = "storage-namespace"
    PLUGIN = "plugin"
    BGTASK = "bgtask"
    LEADER_ELECTION = "leader-election"
    KERNEL = "kernel"
    USER = "user"
    KEYPAIR = "keypair"
    SESSION = "session"
    GROUP = "group"
    DOMAIN = "domain"
    IMAGE = "image"
    IMAGE_ALIAS = "image-alias"
    TEMPLATE = "template"
    CONTAINER_REGISTRY = "container-registry"
    SCALING_GROUP = "scaling-group"
    INSTANCE = "instance"
    ENDPOINT = "endpoint"
    ENDPOINT_AUTO_SCALING = "endpoint-auto-scaling"
    ROUTE = "route"
    DOTFILE = "dotfile"
    VFOLDER = "vfolder"
    VFOLDER_INVITATION = "vfolder-invitation"
    MODEL_CARD = "model-card"
    MODEL_SERVICE = "model-service"
    MODEL_DEPLOYMENT = "model-deployment"
    RESOURCE_PRESET = "resource-preset"
    STORAGE = "storage"
    AGENT = "agent"
    PERMISSION = "permission"
    METRIC = "metric"
    STORAGE_PROXY = "storage-proxy"
    MESSAGE_QUEUE = "message-queue"


class ErrorOperation(enum.StrEnum):
    """
    An enum to represent the operation where the error occurred.
    The operation is a string that represents the action that was being performed
    when the error occurred.
    """

    GENERIC = "generic"  # Whenever possible, use specific operation names instead of this one.
    CREATE = "create"
    ACCESS = "access"
    READ = "read"
    UPDATE = "update"
    START = "start"
    SOFT_DELETE = "soft-delete"
    HARD_DELETE = "purge"
    LIST = "list-query"
    AUTH = "auth"
    HOOK = "hook"
    REQUEST = "request"
    PARSING = "parsing"
    EXECUTE = "execute"
    SCHEDULE = "schedule"
    SETUP = "setup"
    GRANT = "grant"
    CHECK_LIMIT = "check-limit"


class ErrorDetail(enum.StrEnum):
    """
    An enum to represent the specific error that occurred during the operation.
    The error detail is a string that describes the specific error that occurred
    during the operation.
    """

    # Client Error
    BAD_REQUEST = "bad-request"
    NOT_FOUND = "not-found"
    GONE = "gone"  # The resource is gone.
    # Conflict means the request conflicts with the current state of the server.
    CONFLICT = "conflict"
    # Already Exists means the resource already exists.
    ALREADY_EXISTS = "already-exists"
    # Invalid parameters means the received parameters are invalid.
    # This is different from BAD_REQUEST, which means the request is malformed.
    INVALID_PARAMETERS = "invalid-parameters"
    # DATA_EXPIRED means the data is expired and cannot be used anymore.
    # This is different from NOT_FOUND, which means the resource does not exist.
    # For example, the password is expired or the auth token is expired.
    DATA_EXPIRED = "data-expired"
    # Forbidden means the user is not allowed to access the resource.
    # This is different from UNAUTHORIZED, which means the user is not authenticated.
    FORBIDDEN = "forbidden"
    # Unauthorized means the user is not authenticated.
    # This means the user is not logged in or the token is invalid.
    UNAUTHORIZED = "unauthorized"
    # Incomplete user profile means the user profile is not complete.
    # This means the user has not completed the required fields in the profile.
    # For example, the user has not completed a 2FA setup or any verification.
    INCOMPLETE_USER_PROFILE = "incomplete-user-profile"
    NOT_READY = "not-ready"  # The resource is not ready to be used.
    INVALID_DATA_FORMAT = "invalid-data-format"  # The data format is invalid.

    # Server Error
    INTERNAL_ERROR = (
        "internal-error"  # Whenever possible, use specific error names instead of this one.
    )
    # UNAVAILABLE means the resource is not available.
    UNAVAILABLE = "unavailable"
    # UNREACHABLE means the resource is unreachable.
    UNREACHABLE = "unreachable"
    # TIMEOUT means the request timed out.
    TASK_TIMEOUT = "task-timeout"
    CANCELED = "canceled"
    # Unexpected Error
    NOT_IMPLEMENTED = "not-implemented"
    DEPRECATED = "deprecated"
    # MISMATCH means the current state of the server does not match the expected state.
    # MISMATCH is used when the server is in a state that is not expected.
    MISMATCH = "mismatch"


@dataclass
class ErrorCode:
    """
    A dataclass to represent error codes for Backend.AI errors.

    All fields are lowercase.

    The top-level domain is set to backendai. Other domains represent the specific
    area where the error occurred, such as kernel, user, session, etc.
    Whenever possible, use detailed domain names instead of backendai of general purpose errors.

    The operation field represents the operation where the error occurred,
    such as create, delete, update, get, list, etc.

    The error_detail field describes the specific error that occurred during the operation.
    If it consists of two or more words, they should be connected with a hyphen (-).
    """

    domain: ErrorDomain
    operation: ErrorOperation
    error_detail: ErrorDetail

    @classmethod
    def default(cls) -> Self:
        """
        Returns the default error code for Backend.AI errors.
        This is used when the error code is not specified.
        The default error code is `backendai_generic_internal-error`.
        """
        return cls(
            domain=ErrorDomain.BACKENDAI,
            operation=ErrorOperation.GENERIC,
            error_detail=ErrorDetail.INTERNAL_ERROR,
        )

    def __str__(self) -> str:
        return f"{self.domain}_{self.operation}_{self.error_detail}"


class BackendAIError(web.HTTPError, ABC):
    """
    An RFC-7807 error class as a drop-in replacement of the original
    aiohttp.web.HTTPError subclasses.
    """

    error_type: str = "https://api.backend.ai/probs/general-error"
    error_title: str = "General Backend API Error."
    extra_msg: Optional[str]
    body_dict: dict[str, Any]

    def __init__(self, extra_msg: str | None = None, extra_data: Optional[Any] = None, **kwargs):
        super().__init__(**kwargs)
        self.args = (self.status_code, self.reason, self.error_type)
        self.empty_body = False
        self.content_type = "application/problem+json"
        self.extra_msg = extra_msg
        self.extra_data = extra_data
        body = {
            "type": self.error_type,
            "title": self.error_title,
            "error_code": str(self.error_code()),
        }
        if extra_msg is not None:
            body["msg"] = extra_msg
        if extra_data is not None:
            body["data"] = extra_data
        self.body_dict = body
        self.body = dump_json(body)

    def __str__(self):
        lines = []
        if self.extra_msg:
            lines.append(f"{self.error_title} ({self.extra_msg})")
        else:
            lines.append(self.error_title)
        if self.extra_data:
            lines.append(" -> extra_data: " + repr(self.extra_data))
        return "\n".join(lines)

    def __repr__(self):
        lines = []
        if self.extra_msg:
            lines.append(
                f"<{type(self).__name__}({self.status}): {self.error_title} ({self.extra_msg})>"
            )
        else:
            lines.append(f"<{type(self).__name__}({self.status}): {self.error_title}>")
        if self.extra_data:
            lines.append(" -> extra_data: " + repr(self.extra_data))
        return "\n".join(lines)

    def __reduce__(self):
        return (
            type(self),
            (),  # empty the constructor args to make unpickler to use
            # only the exact current state in __dict__
            self.__dict__,
        )

    @classmethod
    @abstractmethod
    def error_code(cls) -> ErrorCode:
        """
        Returns the error code for this error.
        This is used in the API response to indicate the type of error.

        The error code is in the form {domain}_{operation}_{error}.
        For example, "kernel_create_invalid-image" or "kernel_create_timeout".
        """
        raise NotImplementedError("Subclasses must implement error_code() method.")


class MalformedRequestBody(BackendAIError, web.HTTPBadRequest):
    error_type = "https://api.backend.ai/probs/generic-bad-request"
    error_title = "Malformed request body."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.API,
            operation=ErrorOperation.PARSING,
            error_detail=ErrorDetail.BAD_REQUEST,
        )


class InvalidAPIParameters(BackendAIError, web.HTTPBadRequest):
    error_type = "https://api.backend.ai/probs/generic-bad-request"
    error_title = "Invalid or Missing API Parameters."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.API,
            operation=ErrorOperation.PARSING,
            error_detail=ErrorDetail.INVALID_PARAMETERS,
        )


class ResourcePresetConflict(BackendAIError, web.HTTPConflict):
    error_type = "https://api.backend.ai/probs/duplicate-resource"
    error_title = "Duplicate Resource Preset"

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.RESOURCE_PRESET,
            operation=ErrorOperation.GENERIC,
            error_detail=ErrorDetail.CONFLICT,
        )


class MiddlewareParamParsingFailed(BackendAIError, web.HTTPInternalServerError):
    error_type = "https://api.backend.ai/probs/internal-server-error"
    error_title = "Middleware parameter parsing failed."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.API,
            operation=ErrorOperation.PARSING,
            error_detail=ErrorDetail.BAD_REQUEST,
        )


class ParameterNotParsedError(BackendAIError, web.HTTPInternalServerError):
    error_type = "https://api.backend.ai/probs/internal-server-error"
    error_title = "Parameter Not Parsed Error"

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.API,
            operation=ErrorOperation.PARSING,
            error_detail=ErrorDetail.NOT_FOUND,
        )


class BgtaskNotRegisteredError(BackendAIError, web.HTTPInternalServerError):
    error_type = "https://api.backend.ai/probs/bgtask-not-registered"
    error_title = "Background Task Not Registered"

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.BGTASK,
            operation=ErrorOperation.EXECUTE,
            error_detail=ErrorDetail.NOT_IMPLEMENTED,
        )


class BgtaskNotFoundError(BackendAIError, web.HTTPNotFound):
    error_type = "https://api.backend.ai/probs/bgtask-not-found"
    error_title = "Background Task Not Found"

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.BGTASK,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.NOT_FOUND,
        )


class BgtaskFailedError(BackendAIError, web.HTTPInternalServerError):
    error_type = "https://api.backend.ai/probs/bgtask-failed"
    error_title = "Background Task Failed"

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.BGTASK,
            operation=ErrorOperation.EXECUTE,
            error_detail=ErrorDetail.INTERNAL_ERROR,
        )


class BgtaskCancelledError(BackendAIError, web.HTTPInternalServerError):
    error_type = "https://api.backend.ai/probs/bgtask-cancelled"
    error_title = "Background Task Cancelled"

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.BGTASK,
            operation=ErrorOperation.EXECUTE,
            error_detail=ErrorDetail.CANCELED,
        )


class UnreachableError(BackendAIError, web.HTTPInternalServerError):
    error_type = "https://api.backend.ai/probs/unreachable"
    error_title = "Unreachable"

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.BACKENDAI,
            operation=ErrorOperation.GENERIC,
            error_detail=ErrorDetail.UNREACHABLE,
        )


class PermissionDeniedError(BackendAIError, web.HTTPForbidden):
    error_type = "https://api.backend.ai/probs/permission-denied"
    error_title = "Permission Denied."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.API,
            operation=ErrorOperation.AUTH,
            error_detail=ErrorDetail.FORBIDDEN,
        )


class SessionWithInvalidStateError(BackendAIError, web.HTTPConflict):
    error_type = "https://api.backend.ai/probs/session-invalid-state"
    error_title = "Session with Invalid State"

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.SESSION,
            operation=ErrorOperation.GENERIC,
            error_detail=ErrorDetail.MISMATCH,
        )


class StorageNamespaceNotFoundError(BackendAIError, web.HTTPNotFound):
    error_type = "https://api.backend.ai/probs/storage-namespace-not-found"
    error_title = "Storage Namespace Not Found"

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.STORAGE_NAMESPACE,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.NOT_FOUND,
        )


class InvalidCursorTypeError(BackendAIError, web.HTTPBadRequest):
    error_type = "https://api.backend.ai/probs/invalid-cursor-type"
    error_title = "Invalid Cursor Type"

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.BACKENDAI,
            operation=ErrorOperation.REQUEST,
            error_detail=ErrorDetail.BAD_REQUEST,
        )


class RelationNotLoadedError(BackendAIError, web.HTTPInternalServerError):
    error_type = "https://api.backend.ai/probs/relation-not-loaded"
    error_title = "Relation Not Loaded"

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.BACKENDAI,
            operation=ErrorOperation.GENERIC,
            error_detail=ErrorDetail.INTERNAL_ERROR,
        )


class ArtifactDefaultRevisionResolveError(BackendAIError, web.HTTPBadRequest):
    error_type = "https://api.backend.ai/probs/artifact-revision-resolve-failed"
    error_title = "Cannot Resolve Artifact Default Revision"

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.ARTIFACT,
            operation=ErrorOperation.REQUEST,
            error_detail=ErrorDetail.BAD_REQUEST,
        )


class RuntimeVariantNotSupportedError(BackendAIError, web.HTTPBadRequest):
    error_type = "https://api.backend.ai/probs/runtime-variant-not-supported"
    error_title = "Runtime Variant Not Supported"

    def __init__(self, runtime_variant: str) -> None:
        super().__init__(extra_msg=f"Runtime variant '{runtime_variant}' is not supported.")

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.MODEL_DEPLOYMENT,
            operation=ErrorOperation.REQUEST,
            error_detail=ErrorDetail.BAD_REQUEST,
        )


class GenericNotImplementedError(BackendAIError, web.HTTPInternalServerError):
    error_type = "https://api.backend.ai/probs/not-implemented"
    error_title = "Not Implemented"

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.BACKENDAI,
            operation=ErrorOperation.GENERIC,
            error_detail=ErrorDetail.NOT_IMPLEMENTED,
        )


class InvalidConfigError(BackendAIError, web.HTTPInternalServerError):
    error_type = "https://api.backend.ai/probs/invalid-configuration"
    error_title = "Invalid Configuration"

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.BACKENDAI,
            operation=ErrorOperation.GENERIC,
            error_detail=ErrorDetail.INTERNAL_ERROR,
        )


class ProcessorNotReadyError(BackendAIError, web.HTTPInternalServerError):
    error_type = "https://api.backend.ai/probs/processor-not-ready"
    error_title = "Processor Not Ready"

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.BACKENDAI,
            operation=ErrorOperation.GENERIC,
            error_detail=ErrorDetail.INTERNAL_ERROR,
        )


class AgentNotFound(BackendAIError, web.HTTPNotFound):
    error_type = "https://api.backend.ai/probs/agent-not-found"
    error_title = "Agent Not Found"

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.AGENT,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.NOT_FOUND,
        )
