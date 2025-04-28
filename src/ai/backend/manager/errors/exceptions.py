"""
This module defines a series of Backend.AI-specific errors based on HTTP Error
classes from aiohttp.
Raising a BackendError is automatically mapped to a corresponding HTTP error
response with RFC7807-style JSON-encoded description in its response body.

In the client side, you should use "type" field in the body to distinguish
canonical error types beacuse "title" field may change due to localization and
future UX improvements.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING, Any, Optional, Union, cast

from aiohttp import web

from ai.backend.common.exception import (
    BackendAIError as BackendError,
)
from ai.backend.common.exception import (
    ErrorCode,
    ErrorDetail,
    ErrorDomain,
    ErrorOperation,
)
from ai.backend.common.json import dump_json
from ai.backend.common.plugin.hook import HookResult

from ..exceptions import AgentError

if TYPE_CHECKING:
    from ai.backend.manager.api.vfolder import VFolderRow


class URLNotFound(BackendError, web.HTTPNotFound):  # TODO: Misused now.
    error_type = "https://api.backend.ai/probs/url-not-found"
    error_title = "Unknown URL path."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.API,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.NOT_FOUND,
        )


class ObjectNotFound(BackendError, web.HTTPNotFound):
    error_type = "https://api.backend.ai/probs/object-not-found"
    object_name = "object"

    def __init__(
        self,
        extra_msg: Optional[str] = None,
        extra_data: Optional[Any] = None,
        *,
        object_name: Optional[str] = None,
        **kwargs,
    ) -> None:
        if object_name:
            self.object_name = object_name
        self.error_title = f"No such {self.object_name}."
        super().__init__(extra_msg, extra_data, **kwargs)

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.BACKENDAI,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.NOT_FOUND,
        )


class GenericBadRequest(BackendError, web.HTTPBadRequest):
    error_type = "https://api.backend.ai/probs/generic-bad-request"
    error_title = "Bad request."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.BACKENDAI,
            operation=ErrorOperation.GENERIC,
            error_detail=ErrorDetail.BAD_REQUEST,
        )


class RejectedByHook(BackendError, web.HTTPBadRequest):
    error_type = "https://api.backend.ai/probs/rejected-by-hook"
    error_title = "Operation rejected by a hook plugin."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.PLUGIN,
            operation=ErrorOperation.HOOK,
            error_detail=ErrorDetail.FORBIDDEN,
        )

    @classmethod
    def from_hook_result(cls, result: HookResult) -> RejectedByHook:
        return cls(
            extra_msg=result.reason,
            extra_data={
                "plugins": result.src_plugin,
            },
        )


class InvalidCredentials(BackendError, web.HTTPBadRequest):
    error_type = "https://api.backend.ai/probs/invalid-credentials"
    error_title = "Invalid credentials for authentication."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.USER,
            operation=ErrorOperation.AUTH,
            error_detail=ErrorDetail.INVALID_PARAMETERS,
        )


class GenericForbidden(BackendError, web.HTTPForbidden):
    error_type = "https://api.backend.ai/probs/generic-forbidden"
    error_title = "Forbidden operation."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.BACKENDAI,
            operation=ErrorOperation.GENERIC,
            error_detail=ErrorDetail.FORBIDDEN,
        )


class InsufficientPrivilege(BackendError, web.HTTPForbidden):
    error_type = "https://api.backend.ai/probs/insufficient-privilege"
    error_title = "Insufficient privilege."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.USER,
            operation=ErrorOperation.AUTH,
            error_detail=ErrorDetail.FORBIDDEN,
        )


class MethodNotAllowed(BackendError, web.HTTPMethodNotAllowed):
    error_type = "https://api.backend.ai/probs/method-not-allowed"
    error_title = "HTTP Method Not Allowed."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.API,
            operation=ErrorOperation.ACCESS,
            error_detail=ErrorDetail.FORBIDDEN,
        )


class InternalServerError(BackendError, web.HTTPInternalServerError):
    error_type = "https://api.backend.ai/probs/internal-server-error"
    error_title = "Internal server error."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.BACKENDAI,
            operation=ErrorOperation.GENERIC,
            error_detail=ErrorDetail.INTERNAL_ERROR,
        )


class ServerMisconfiguredError(BackendError, web.HTTPInternalServerError):
    error_type = "https://api.backend.ai/probs/server-misconfigured"
    error_title = "Service misconfigured."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.BACKENDAI,
            operation=ErrorOperation.SETUP,
            error_detail=ErrorDetail.INTERNAL_ERROR,
        )


class ServiceUnavailable(BackendError, web.HTTPServiceUnavailable):
    error_type = "https://api.backend.ai/probs/service-unavailable"
    error_title = "Serivce unavailable."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.BACKENDAI,
            operation=ErrorOperation.GENERIC,
            error_detail=ErrorDetail.UNAVAILABLE,
        )


class NotImplementedAPI(BackendError, web.HTTPBadRequest):
    error_type = "https://api.backend.ai/probs/not-implemented"
    error_title = "This API is not implemented."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.API,
            operation=ErrorOperation.GENERIC,
            error_detail=ErrorDetail.NOT_IMPLEMENTED,
        )


class DeprecatedAPI(BackendError, web.HTTPBadRequest):
    error_type = "https://api.backend.ai/probs/deprecated"
    error_title = "This API is deprecated."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.API,
            operation=ErrorOperation.GENERIC,
            error_detail=ErrorDetail.DEPRECATED,
        )


class InvalidAuthParameters(BackendError, web.HTTPBadRequest):
    error_type = "https://api.backend.ai/probs/invalid-auth-params"
    error_title = "Missing or invalid authorization parameters."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.USER,
            operation=ErrorOperation.AUTH,
            error_detail=ErrorDetail.INVALID_PARAMETERS,
        )


class AuthorizationFailed(BackendError, web.HTTPUnauthorized):
    error_type = "https://api.backend.ai/probs/auth-failed"
    error_title = "Credential/signature mismatch."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.USER,
            operation=ErrorOperation.AUTH,
            error_detail=ErrorDetail.UNAUTHORIZED,
        )


class PasswordExpired(BackendError, web.HTTPUnauthorized):
    error_type = "https://api.backend.ai/probs/password-expired"
    error_title = "Password has expired."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.USER,
            operation=ErrorOperation.AUTH,
            error_detail=ErrorDetail.DATA_EXPIRED,
        )


class InvalidAPIParameters(BackendError, web.HTTPBadRequest):
    error_type = "https://api.backend.ai/probs/invalid-api-params"
    error_title = "Missing or invalid API parameters."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.API,
            operation=ErrorOperation.GENERIC,
            error_detail=ErrorDetail.INVALID_PARAMETERS,
        )


class GraphQLError(BackendError, web.HTTPBadRequest):
    error_type = "https://api.backend.ai/probs/graphql-error"
    error_title = "GraphQL-generated error."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.API,
            operation=ErrorOperation.GENERIC,
            error_detail=ErrorDetail.INTERNAL_ERROR,
        )


class ContainerRegistryWebhookAuthorizationFailed(BackendError, web.HTTPUnauthorized):
    error_type = "https://api.backend.ai/probs/webhook/auth-failed"
    error_title = "Container Registry Webhook authorization failed."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.CONTAINER_REGISTRY,
            operation=ErrorOperation.HOOK,
            error_detail=ErrorDetail.UNAUTHORIZED,
        )


class HarborWebhookContainerRegistryRowNotFound(InternalServerError):
    error_type = "https://api.backend.ai/probs/webhook/harbor/container-registry-not-found"
    error_title = "Container registry row not found."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.CONTAINER_REGISTRY,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.NOT_FOUND,
        )


class InstanceNotFound(ObjectNotFound):
    object_name = "agent instance"

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.INSTANCE,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.NOT_FOUND,
        )


class ImageNotFound(ObjectNotFound):
    object_name = "environment image"

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.IMAGE,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.NOT_FOUND,
        )


class DomainNotFound(ObjectNotFound):
    object_name = "domain"

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.DOMAIN,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.NOT_FOUND,
        )


class GroupNotFound(ObjectNotFound):
    object_name = "user group (or project)"

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.GROUP,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.NOT_FOUND,
        )


class UserNotFound(ObjectNotFound):
    object_name = "user"

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.USER,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.NOT_FOUND,
        )


class ScalingGroupNotFound(ObjectNotFound):
    object_name = "scaling group"

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.SCALING_GROUP,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.NOT_FOUND,
        )


class SessionNotFound(ObjectNotFound):
    object_name = "session"

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.SESSION,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.NOT_FOUND,
        )


class MainKernelNotFound(ObjectNotFound):
    object_name = "main kernel"

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.KERNEL,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.NOT_FOUND,
        )


class KernelNotFound(ObjectNotFound):
    object_name = "kernel"

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.KERNEL,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.NOT_FOUND,
        )


class EndpointNotFound(ObjectNotFound):
    object_name = "endpoint"

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.ENDPOINT,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.NOT_FOUND,
        )


class RoutingNotFound(ObjectNotFound):
    object_name = "routing"

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.ROUTE,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.NOT_FOUND,
        )


class EndpointTokenNotFound(ObjectNotFound):
    object_name = "endpoint_token"

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.ENDPOINT,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.NOT_FOUND,
        )


class ContainerRegistryNotFound(ObjectNotFound):
    object_name = "container_registry"

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.CONTAINER_REGISTRY,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.NOT_FOUND,
        )


class ContainerRegistryGroupsAssociationNotFound(ObjectNotFound):
    object_name = "association of container_registry and group"

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.CONTAINER_REGISTRY,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.NOT_FOUND,
        )


class TooManySessionsMatched(BackendError, web.HTTPNotFound):
    error_type = "https://api.backend.ai/probs/too-many-sessions-matched"
    error_title = "Too many sessions matched."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.SESSION,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.CONFLICT,
        )

    def __init__(
        self,
        extra_msg: Optional[str] = None,
        extra_data: Optional[dict[str, Any]] = None,
        **kwargs,
    ):
        if extra_data is not None and (matches := extra_data.get("matches", None)) is not None:
            serializable_matches = [
                {
                    "id": str(item["session_id"]),
                    "name": item["session_name"],
                    "status": item["status"].name,
                    "created_at": item["created_at"].isoformat(),
                }
                for item in matches
            ]
            extra_data["matches"] = serializable_matches
        super().__init__(extra_msg, extra_data, **kwargs)


class TooManyKernelsFound(BackendError, web.HTTPNotFound):
    error_type = "https://api.backend.ai/probs/too-many-kernels"
    error_title = "There are two or more matching kernels."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.KERNEL,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.CONFLICT,
        )


class TaskTemplateNotFound(ObjectNotFound):
    object_name = "task template"

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.TEMPLATE,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.NOT_FOUND,
        )


class AppNotFound(ObjectNotFound):
    object_name = "app service"

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.BACKENDAI,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.NOT_FOUND,
        )


class SessionAlreadyExists(BackendError, web.HTTPBadRequest):
    error_type = "https://api.backend.ai/probs/session-already-exists"
    error_title = "The session already exists but you requested not to reuse existing one."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.SESSION,
            operation=ErrorOperation.CREATE,
            error_detail=ErrorDetail.ALREADY_EXISTS,
        )


class TooManyVFoldersFound(BackendError, web.HTTPNotFound):
    error_type = "https://api.backend.ai/probs/too-many-vfolders"
    error_title = "Multiple vfolders found for the operation for a single vfolder."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.VFOLDER,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.CONFLICT,
        )

    def __init__(self, matched_rows: Sequence[VFolderRow]) -> None:
        serialized_matches = [
            {
                "id": row["id"],
                "host": row["host"],
                "user": row["user_email"],
                "user_id": row["user"],
                "group": row["group_name"],
                "group_id": row["group"],
            }
            for row in matched_rows
        ]
        super().__init__(extra_data={"matches": serialized_matches})


class VFolderNotFound(ObjectNotFound):
    object_name = "virtual folder"

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.VFOLDER,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.NOT_FOUND,
        )


class VFolderAlreadyExists(BackendError, web.HTTPBadRequest):
    error_type = "https://api.backend.ai/probs/vfolder-already-exists"
    error_title = "The virtual folder already exists with the same name."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.VFOLDER,
            operation=ErrorOperation.CREATE,
            error_detail=ErrorDetail.ALREADY_EXISTS,
        )


class ModelServiceDependencyNotCleared(BackendError, web.HTTPBadRequest):
    error_title = "Cannot delete model VFolders bound to alive model services."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.MODEL_SERVICE,
            operation=ErrorOperation.SOFT_DELETE,
            error_detail=ErrorDetail.CONFLICT,
        )


class VFolderOperationFailed(BackendError, web.HTTPBadRequest):
    error_type = "https://api.backend.ai/probs/vfolder-operation-failed"
    error_title = "Virtual folder operation has failed."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.VFOLDER,
            operation=ErrorOperation.GENERIC,
            error_detail=ErrorDetail.INTERNAL_ERROR,
        )


class VFolderFilterStatusFailed(BackendError, web.HTTPBadRequest):
    error_type = "https://api.backend.ai/probs/vfolder-filter-status-failed"
    error_title = "Virtual folder status filtering has failed."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.VFOLDER,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.BAD_REQUEST,
        )


class VFolderFilterStatusNotAvailable(BackendError, web.HTTPBadRequest):
    error_type = "https://api.backend.ai/probs/vfolder-filter-status-not-available"
    error_title = "There is no available virtual folder to filter its status."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.VFOLDER,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.INTERNAL_ERROR,
        )


class VFolderPermissionError(BackendError, web.HTTPBadRequest):
    error_type = "https://api.backend.ai/probs/vfolder-permission-error"
    error_title = "The virtual folder does not permit the specified permission."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.VFOLDER,
            operation=ErrorOperation.ACCESS,
            error_detail=ErrorDetail.FORBIDDEN,
        )


class DotfileCreationFailed(BackendError, web.HTTPBadRequest):
    error_type = "https://api.backend.ai/probs/generic-bad-request"
    error_title = "Dotfile creation has failed."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.DOTFILE,
            operation=ErrorOperation.CREATE,
            error_detail=ErrorDetail.INTERNAL_ERROR,
        )


class DotfileAlreadyExists(BackendError, web.HTTPBadRequest):
    error_type = "https://api.backend.ai/probs/generic-bad-request"
    error_title = "Dotfile already exists."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.DOTFILE,
            operation=ErrorOperation.CREATE,
            error_detail=ErrorDetail.ALREADY_EXISTS,
        )


class DotfileNotFound(ObjectNotFound):
    object_name = "dotfile"

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.DOTFILE,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.NOT_FOUND,
        )


class DotfileVFolderPathConflict(BackendError, web.HTTPBadRequest):
    error_type = "https://api.backend.ai/probs/dotfile-vfolder-path-conflict"
    error_title = "The dotfile path conflicts with a virtual folder path."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.DOTFILE,
            operation=ErrorOperation.CREATE,
            error_detail=ErrorDetail.CONFLICT,
        )


class QuotaExceeded(BackendError, web.HTTPPreconditionFailed):
    error_type = "https://api.backend.ai/probs/quota-exceeded"
    error_title = "You have reached your resource limit."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.SESSION,
            operation=ErrorOperation.CREATE,
            error_detail=ErrorDetail.UNAVAILABLE,
        )


class RateLimitExceeded(BackendError, web.HTTPTooManyRequests):
    error_type = "https://api.backend.ai/probs/rate-limit-exceeded"
    error_title = "You have reached your API query rate limit."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.API,
            operation=ErrorOperation.ACCESS,
            error_detail=ErrorDetail.UNAVAILABLE,
        )


class InstanceNotAvailable(BackendError, web.HTTPServiceUnavailable):
    error_type = "https://api.backend.ai/probs/instance-not-available"
    error_title = "There is no available instance."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.INSTANCE,
            operation=ErrorOperation.ACCESS,
            error_detail=ErrorDetail.UNAVAILABLE,
        )


class ServerFrozen(BackendError, web.HTTPServiceUnavailable):
    error_type = "https://api.backend.ai/probs/server-frozen"
    error_title = "The server is frozen due to maintenance. Please try again later."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.API,
            operation=ErrorOperation.ACCESS,
            error_detail=ErrorDetail.UNAVAILABLE,
        )


class StorageProxyError(BackendError, web.HTTPError):
    error_type = "https://api.backend.ai/probs/storage-proxy-error"
    error_title = "The storage proxy returned an error."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.STORAGE,
            operation=ErrorOperation.ACCESS,
            error_detail=ErrorDetail.INTERNAL_ERROR,
        )

    def __init__(self, status: int, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        # Currently there is no good public way to override the status code
        # after initialization of aiohttp.web.StreamResponse objects. :(
        self.status_code = status  # HTTPException uses self.status_code
        self._status = status  # StreamResponse uses self._status
        self.args = (status, self.args[1], self.args[2])

    @property
    def status(self) -> int:
        # override the status property again to refer the subclass' attribute.
        return self.status_code


class BackendAgentError(BackendError):
    """
    An RFC-7807 error class that wraps agent-side errors.
    """

    _short_type_map = {
        "TIMEOUT": "https://api.backend.ai/probs/agent-timeout",
        "INVALID_INPUT": "https://api.backend.ai/probs/agent-invalid-input",
        "FAILURE": "https://api.backend.ai/probs/agent-failure",
    }

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.AGENT,
            operation=ErrorOperation.ACCESS,
            error_detail=ErrorDetail.INTERNAL_ERROR,
        )

    def __init__(
        self,
        agent_error_type: str,
        exc_info: Union[str, AgentError, Exception, Mapping[str, Optional[str]], None] = None,
    ):
        super().__init__()
        agent_details: Mapping[str, Optional[str]]
        if not agent_error_type.startswith("https://"):
            agent_error_type = self._short_type_map[agent_error_type.upper()]
        self.args = (
            self.status_code,
            self.reason,
            self.error_type,
            agent_error_type,
        )
        if isinstance(exc_info, str):
            agent_details = {
                "type": agent_error_type,
                "title": exc_info,
            }
        elif isinstance(exc_info, AgentError):
            e = cast(AgentError, exc_info)
            agent_details = {
                "type": agent_error_type,
                "title": "Agent-side exception occurred.",
                "exception": e.exc_repr,
            }
        elif isinstance(exc_info, Exception):
            agent_details = {
                "type": agent_error_type,
                "title": "Unexpected exception ocurred.",
                "exception": repr(exc_info),
            }
        elif isinstance(exc_info, Mapping):
            agent_details = exc_info
        else:
            agent_details = {
                "type": agent_error_type,
                "title": None if exc_info is None else str(exc_info),
            }
        self.agent_details = agent_details
        self.agent_error_type = agent_error_type
        self.agent_error_title = agent_details["title"]
        self.agent_exception = agent_details.get("exception", "")
        self.body = dump_json({
            "type": self.error_type,
            "title": self.error_title,
            "agent-details": agent_details,
        })

    def __str__(self):
        if self.agent_exception:
            return f"{self.agent_error_title} ({self.agent_exception})"
        return f"{self.agent_error_title}"

    def __repr__(self):
        if self.agent_exception:
            return f"<{type(self).__name__}: {self.agent_error_title} ({self.agent_exception})>"
        return f"<{type(self).__name__}: {self.agent_error_title}>"

    def __reduce__(self):
        return (type(self), (self.agent_error_type, self.agent_details))


class KernelCreationFailed(BackendAgentError, web.HTTPInternalServerError):
    error_type = "https://api.backend.ai/probs/kernel-creation-failed"
    error_title = "Kernel creation has failed."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.KERNEL,
            operation=ErrorOperation.CREATE,
            error_detail=ErrorDetail.INTERNAL_ERROR,
        )


class KernelDestructionFailed(BackendAgentError, web.HTTPInternalServerError):
    error_type = "https://api.backend.ai/probs/kernel-destruction-failed"
    error_title = "Kernel destruction has failed."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.KERNEL,
            operation=ErrorOperation.SOFT_DELETE,
            error_detail=ErrorDetail.INTERNAL_ERROR,
        )


class KernelRestartFailed(BackendAgentError, web.HTTPInternalServerError):
    error_type = "https://api.backend.ai/probs/kernel-restart-failed"
    error_title = "Kernel restart has failed."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.KERNEL,
            operation=ErrorOperation.START,
            error_detail=ErrorDetail.INTERNAL_ERROR,
        )


class KernelExecutionFailed(BackendAgentError, web.HTTPInternalServerError):
    error_type = "https://api.backend.ai/probs/kernel-execution-failed"
    error_title = "Executing user code in the kernel has failed."

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.KERNEL,
            operation=ErrorOperation.EXECUTE,
            error_detail=ErrorDetail.INTERNAL_ERROR,
        )


class UnknownImageReferenceError(ObjectNotFound):
    object_name = "image reference"

    @classmethod
    def error_code(cls) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.IMAGE,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.INTERNAL_ERROR,
        )
