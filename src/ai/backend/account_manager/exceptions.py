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
from typing import Any, Optional

from aiohttp import web


class BackendError(web.HTTPError):
    """
    An RFC-7807 error class as a drop-in replacement of the original
    aiohttp.web.HTTPError subclasses.
    """

    error_type: str = "https://api.backend.ai/probs/general-error"
    error_title: str = "General Backend API Error."

    content_type: str
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
        }
        if extra_msg is not None:
            body["msg"] = extra_msg
        if extra_data is not None:
            body["data"] = extra_data
        self.body_dict = body
        self.body = json.dumps(body).encode()

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
        *,
        extra_msg: str | None = None,
        extra_data: Optional[Any] = None,
        object_name: str | None = None,
        **kwargs,
    ) -> None:
        if object_name:
            self.object_name = object_name
        self.error_title = f"E00002: No such {self.object_name}."
        super().__init__(extra_msg, extra_data, **kwargs)


class AuthorizationFailed(BackendError, web.HTTPUnauthorized):
    error_type = "https://api.backend.ai/probs/auth-failed"
    error_title = "Credential/signature mismatch."


class InvalidAPIParameters(BackendError, web.HTTPBadRequest):
    error_type = "https://api.backend.ai/probs/invalid-api-params"
    error_title = "Missing or invalid API parameters."


class GenericBadRequest(BackendError, web.HTTPBadRequest):
    error_type = "https://api.backend.ai/probs/generic-bad-request"
    error_title = "Bad request."


class GenericForbidden(BackendError, web.HTTPForbidden):
    error_type = "https://api.backend.ai/probs/generic-forbidden"
    error_title = "Forbidden operation."


class MethodNotAllowed(BackendError, web.HTTPMethodNotAllowed):
    error_type = "https://api.backend.ai/probs/method-not-allowed"
    error_title = "HTTP Method Not Allowed."


class InternalServerError(BackendError, web.HTTPInternalServerError):
    error_type = "https://api.backend.ai/probs/internal-server-error"
    error_title = "Internal server error."


class DatabaseError(BackendError):
    error_title = "error while communicating with database"
