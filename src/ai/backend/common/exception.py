from typing import Any, Mapping


class ConfigurationError(Exception):
    invalid_data: Mapping[str, Any]

    def __init__(self, invalid_data: Mapping[str, Any]) -> None:
        super().__init__(invalid_data)
        self.invalid_data = invalid_data


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
