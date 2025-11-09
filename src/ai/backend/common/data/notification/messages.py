"""Type-safe message models for notification system."""

from __future__ import annotations

from abc import abstractmethod
from collections.abc import Mapping
from typing import Any

from pydantic import BaseModel, Field

from .types import NotificationRuleType

__all__ = (
    "NotifiableMessage",
    "SessionStartedMessage",
    "SessionTerminatedMessage",
    "ArtifactDownloadCompletedMessage",
)


class NotifiableMessage(BaseModel):
    """Base class for all notification messages.

    All notification messages must inherit from this class and define
    their specific fields with comprehensive descriptions.
    """

    model_config = {"extra": "forbid"}  # Strict validation - reject unknown fields

    _register_dict: dict[NotificationRuleType, type["NotifiableMessage"]] = {}

    def __init_subclass__(cls):
        """Automatically register subclasses by their rule type."""
        try:
            rule_type = cls.rule_type()
            if rule_type in cls._register_dict:
                raise RuntimeError(f"Notification message type {rule_type} is already registered")
            cls._register_dict[rule_type] = cls
        except NotImplementedError:
            # If rule_type is not implemented, we cannot register it
            return

    @classmethod
    @abstractmethod
    def rule_type(cls) -> NotificationRuleType:
        """Return the notification rule type for this message class."""
        raise NotImplementedError

    @classmethod
    def validate_notification_data(
        cls,
        rule_type: NotificationRuleType,
        data: Mapping[str, Any],
    ) -> "NotifiableMessage":
        """Validate notification data against the appropriate message type.

        Args:
            rule_type: The type of notification rule
            data: Raw notification data dictionary to validate

        Returns:
            Validated NotifiableMessage instance of the appropriate type

        Raises:
            KeyError: If the rule_type has no associated message class
            ValidationError: If the data doesn't match the message schema
        """
        model_class = cls._register_dict[rule_type]
        return model_class.model_validate(data)

    @classmethod
    def get_message_schema(cls, rule_type: NotificationRuleType) -> dict[str, Any]:
        """Get JSON schema for a notification rule type's message format.

        Args:
            rule_type: The type of notification rule

        Returns:
            JSON schema dictionary describing the message format

        Raises:
            KeyError: If the rule_type has no associated message class
        """
        model_class = cls._register_dict[rule_type]
        return model_class.model_json_schema()


class SessionStartedMessage(NotifiableMessage):
    """Notification message for session start events.

    This message is sent when a compute session successfully starts.
    """

    @classmethod
    def rule_type(cls) -> NotificationRuleType:
        """Return the notification rule type for this message class."""
        return NotificationRuleType.SESSION_STARTED

    session_id: str = Field(description="Unique identifier of the compute session that was started")
    user_name: str = Field(description="Name of the user who started the session")
    kernel_image: str = Field(
        description="Container image used for the session (e.g., 'python:3.11-ubuntu20.04')"
    )
    session_name: str | None = Field(
        default=None, description="User-defined name for the session, if provided"
    )
    access_key: str | None = Field(
        default=None, description="Access key used to create the session"
    )
    cluster_size: int = Field(
        default=1,
        description="Number of containers in the session cluster (1 for single-container sessions)",
    )


class SessionTerminatedMessage(NotifiableMessage):
    """Notification message for session termination events.

    This message is sent when a compute session is terminated,
    either by user request or system action.
    """

    @classmethod
    def rule_type(cls) -> NotificationRuleType:
        """Return the notification rule type for this message class."""
        return NotificationRuleType.SESSION_TERMINATED

    class UserInfo(BaseModel):
        """User information nested in termination message."""

        name: str = Field(description="Name of the user who owned the session")
        id: str = Field(description="Unique identifier of the user")

    class ResourceInfo(BaseModel):
        """Resource information nested in termination message."""

        type: str = Field(description="Type of resource (e.g., 'cpu', 'memory', 'gpu')")
        limit: int = Field(description="Resource limit value that was allocated to the session")

    session_id: str = Field(
        description="Unique identifier of the compute session that was terminated"
    )
    user: UserInfo = Field(description="Information about the user who owned the session")
    resource: ResourceInfo = Field(
        description="Information about resources that were allocated to the session"
    )
    termination_reason: str | None = Field(
        default=None,
        description="Reason for termination (e.g., 'user-requested', 'timeout', 'error')",
    )
    status: str = Field(
        description="Final status of the session (e.g., 'terminated', 'cancelled', 'error')"
    )


class ArtifactDownloadCompletedMessage(NotifiableMessage):
    """Notification message for artifact download completion events.

    This message is sent when an artifact download operation completes.
    """

    @classmethod
    def rule_type(cls) -> NotificationRuleType:
        """Return the notification rule type for this message class."""
        return NotificationRuleType.ARTIFACT_DOWNLOAD_COMPLETED

    artifact_id: str = Field(description="Unique identifier of the downloaded artifact")
    download_url: str | None = Field(
        default=None, description="URL where the artifact was downloaded from, if available"
    )
    file_name: str = Field(description="Name of the downloaded artifact file")
    file_size: int = Field(description="Size of the downloaded artifact in bytes")
    download_status: str = Field(
        description="Status of the download operation (e.g., 'completed', 'failed')"
    )
    user_name: str = Field(description="Name of the user who initiated the download")
