import json
from typing import Any, Mapping, Optional

from aiohttp import web


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


class MalformedRequestBody(BackendError, web.HTTPBadRequest):
    error_type = "https://api.backend.ai/probs/generic-bad-request"
    error_title = "Malformed request body."


class InvalidAPIParameters(BackendError, web.HTTPBadRequest):
    error_type = "https://api.backend.ai/probs/generic-bad-request"
    error_title = "Invalid or Missing API Parameters."


class MiddlewareParamParsingFailed(BackendError, web.HTTPInternalServerError):
    error_type = "https://api.backend.ai/probs/internal-server-error"
    error_title = "Middleware parameter parsing failed."


class ParameterNotParsedError(BackendError, web.HTTPInternalServerError):
    error_type = "https://api.backend.ai/probs/internal-server-error"
    error_title = "Parameter Not Parsed Error"
