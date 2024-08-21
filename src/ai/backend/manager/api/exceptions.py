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

import json
from typing import Any, Dict, Mapping, Optional, Union, cast

from aiohttp import web

from ai.backend.common.json import ExtendedJSONEncoder
from ai.backend.common.plugin.hook import HookResult

from ..exceptions import AgentError


class BackendError(web.HTTPError):
    """
    An RFC-7807 error class as a drop-in replacement of the original
    aiohttp.web.HTTPError subclasses.
    """

    error_type: str = "https://api.backend.ai/probs/general-error"
    error_title: str = "General Backend API Error."

    content_type: str
    extra_msg: Optional[str]

    def __init__(self, extra_msg: str = None, extra_data: Any = None, **kwargs):
        super().__init__(**kwargs)
        self.args = (self.status_code, self.reason, self.error_type)
        self.empty_body = False
        self.content_type = "application/problem+json"
        self.extra_msg = extra_msg
        self.extra_data = extra_data
        body = {
            "type": self.error_type,
            "title": self.error_title,
        }
        if extra_msg is not None:
            body["msg"] = extra_msg
        if extra_data is not None:
            body["data"] = extra_data
        self.body = json.dumps(body, cls=ExtendedJSONEncoder).encode()

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


class URLNotFound(BackendError, web.HTTPNotFound):
    error_type = "https://api.backend.ai/probs/url-not-found"
    error_title = "Unknown URL path."


class ObjectNotFound(BackendError, web.HTTPNotFound):
    error_type = "https://api.backend.ai/probs/object-not-found"
    object_name = "object"

    def __init__(
        self,
        extra_msg: str = None,
        extra_data: Any = None,
        *,
        object_name: str = None,
        **kwargs,
    ) -> None:
        if object_name:
            self.object_name = object_name
        self.error_title = f"No such {self.object_name}."
        super().__init__(extra_msg, extra_data, **kwargs)


class GenericBadRequest(BackendError, web.HTTPBadRequest):
    error_type = "https://api.backend.ai/probs/generic-bad-request"
    error_title = "Bad request."


class RejectedByHook(BackendError, web.HTTPBadRequest):
    error_type = "https://api.backend.ai/probs/rejected-by-hook"
    error_title = "Operation rejected by a hook plugin."

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


class GenericForbidden(BackendError, web.HTTPForbidden):
    error_type = "https://api.backend.ai/probs/generic-forbidden"
    error_title = "Forbidden operation."


class InsufficientPrivilege(BackendError, web.HTTPForbidden):
    error_type = "https://api.backend.ai/probs/insufficient-privilege"
    error_title = "Insufficient privilege."


class MethodNotAllowed(BackendError, web.HTTPMethodNotAllowed):
    error_type = "https://api.backend.ai/probs/method-not-allowed"
    error_title = "HTTP Method Not Allowed."


class InternalServerError(BackendError, web.HTTPInternalServerError):
    error_type = "https://api.backend.ai/probs/internal-server-error"
    error_title = "Internal server error."


class ServerMisconfiguredError(BackendError, web.HTTPInternalServerError):
    error_type = "https://api.backend.ai/probs/server-misconfigured"
    error_title = "Service misconfigured."


class ServiceUnavailable(BackendError, web.HTTPServiceUnavailable):
    error_type = "https://api.backend.ai/probs/service-unavailable"
    error_title = "Serivce unavailable."


class NotImplementedAPI(BackendError, web.HTTPBadRequest):
    error_type = "https://api.backend.ai/probs/not-implemented"
    error_title = "This API is not implemented."


class DeprecatedAPI(BackendError, web.HTTPBadRequest):
    error_type = "https://api.backend.ai/probs/deprecated"
    error_title = "This API is deprecated."


class InvalidAuthParameters(BackendError, web.HTTPBadRequest):
    error_type = "https://api.backend.ai/probs/invalid-auth-params"
    error_title = "Missing or invalid authorization parameters."


class AuthorizationFailed(BackendError, web.HTTPUnauthorized):
    error_type = "https://api.backend.ai/probs/auth-failed"
    error_title = "Credential/signature mismatch."


class PasswordExpired(BackendError, web.HTTPUnauthorized):
    error_type = "https://api.backend.ai/probs/password-expired"
    error_title = "Password has expired."


class InvalidAPIParameters(BackendError, web.HTTPBadRequest):
    error_type = "https://api.backend.ai/probs/invalid-api-params"
    error_title = "Missing or invalid API parameters."


class GraphQLError(BackendError, web.HTTPBadRequest):
    error_type = "https://api.backend.ai/probs/graphql-error"
    error_title = "GraphQL-generated error."


class InstanceNotFound(ObjectNotFound):
    object_name = "agent instance"


class ImageNotFound(ObjectNotFound):
    object_name = "environment image"


class DomainNotFound(ObjectNotFound):
    object_name = "domain"


class GroupNotFound(ObjectNotFound):
    object_name = "user group (or project)"


class UserNotFound(ObjectNotFound):
    object_name = "user"


class ScalingGroupNotFound(ObjectNotFound):
    object_name = "scaling group"


class SessionNotFound(ObjectNotFound):
    object_name = "session"


class MainKernelNotFound(ObjectNotFound):
    object_name = "main kernel"


class KernelNotFound(ObjectNotFound):
    object_name = "kernel"


class EndpointNotFound(ObjectNotFound):
    object_name = "endpoint"


class RoutingNotFound(ObjectNotFound):
    object_name = "routing"


class EndpointTokenNotFound(ObjectNotFound):
    object_name = "endpoint_token"


class TooManySessionsMatched(BackendError, web.HTTPNotFound):
    error_type = "https://api.backend.ai/probs/too-many-sessions-matched"
    error_title = "Too many sessions matched."

    def __init__(self, extra_msg: str = None, extra_data: Dict[str, Any] = None, **kwargs):
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


class TaskTemplateNotFound(ObjectNotFound):
    object_name = "task template"


class AppNotFound(ObjectNotFound):
    object_name = "app service"


class SessionAlreadyExists(BackendError, web.HTTPBadRequest):
    error_type = "https://api.backend.ai/probs/session-already-exists"
    error_title = "The session already exists but you requested not to reuse existing one."


class VFolderCreationFailed(BackendError, web.HTTPBadRequest):
    error_type = "https://api.backend.ai/probs/vfolder-creation-failed"
    error_title = "Virtual folder creation has failed."


class TooManyVFoldersFound(BackendError, web.HTTPNotFound):
    error_type = "https://api.backend.ai/probs/too-many-vfolders"
    error_title = "There are two or more matching vfolders."


class VFolderNotFound(ObjectNotFound):
    object_name = "virtual folder"


class VFolderAlreadyExists(BackendError, web.HTTPBadRequest):
    error_type = "https://api.backend.ai/probs/vfolder-already-exists"
    error_title = "The virtual folder already exists with the same name."


class ModelServiceDependencyNotCleared(BackendError, web.HTTPBadRequest):
    error_title = "Cannot delete model VFolders bound to alive model services."


class VFolderOperationFailed(BackendError, web.HTTPBadRequest):
    error_type = "https://api.backend.ai/probs/vfolder-operation-failed"
    error_title = "Virtual folder operation has failed."


class VFolderFilterStatusFailed(BackendError, web.HTTPBadRequest):
    error_type = "https://api.backend.ai/probs/vfolder-filter-status-failed"
    error_title = "Virtual folder status filtering has failed."


class VFolderFilterStatusNotAvailable(BackendError, web.HTTPBadRequest):
    error_type = "https://api.backend.ai/probs/vfolder-filter-status-not-available"
    error_title = "There is no available virtual folder to filter its status."


class VFolderPermissionError(BackendError, web.HTTPBadRequest):
    error_type = "https://api.backend.ai/probs/vfolder-permission-error"
    error_title = "The virtual folder does not permit the specified permission."


class DotfileCreationFailed(BackendError, web.HTTPBadRequest):
    error_type = "https://api.backend.ai/probs/generic-bad-request"
    error_title = "Dotfile creation has failed."


class DotfileAlreadyExists(BackendError, web.HTTPBadRequest):
    error_type = "https://api.backend.ai/probs/generic-bad-request"
    error_title = "Dotfile already exists."


class DotfileNotFound(ObjectNotFound):
    object_name = "dotfile"


class QuotaExceeded(BackendError, web.HTTPPreconditionFailed):
    error_type = "https://api.backend.ai/probs/quota-exceeded"
    error_title = "You have reached your resource limit."


class RateLimitExceeded(BackendError, web.HTTPTooManyRequests):
    error_type = "https://api.backend.ai/probs/rate-limit-exceeded"
    error_title = "You have reached your API query rate limit."


class InstanceNotAvailable(BackendError, web.HTTPServiceUnavailable):
    error_type = "https://api.backend.ai/probs/instance-not-available"
    error_title = "There is no available instance."


class ServerFrozen(BackendError, web.HTTPServiceUnavailable):
    error_type = "https://api.backend.ai/probs/server-frozen"
    error_title = "The server is frozen due to maintenance. Please try again later."


class StorageProxyError(BackendError, web.HTTPError):
    error_type = "https://api.backend.ai/probs/storage-proxy-error"
    error_title = "The storage proxy returned an error."

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
        self.body = json.dumps({
            "type": self.error_type,
            "title": self.error_title,
            "agent-details": agent_details,
        }).encode()

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


class KernelDestructionFailed(BackendAgentError, web.HTTPInternalServerError):
    error_type = "https://api.backend.ai/probs/kernel-destruction-failed"
    error_title = "Kernel destruction has failed."


class KernelRestartFailed(BackendAgentError, web.HTTPInternalServerError):
    error_type = "https://api.backend.ai/probs/kernel-restart-failed"
    error_title = "Kernel restart has failed."


class KernelExecutionFailed(BackendAgentError, web.HTTPInternalServerError):
    error_type = "https://api.backend.ai/probs/kernel-execution-failed"
    error_title = "Executing user code in the kernel has failed."


class UnknownImageReferenceError(ObjectNotFound):
    object_name = "image reference"
