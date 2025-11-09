"""Type-safe message models for notification system."""

from __future__ import annotations

from abc import abstractmethod
from collections.abc import Mapping
from typing import Any, Optional

from pydantic import BaseModel, Field

from .types import NotificationRuleType

__all__ = (
    "NotifiableMessage",
    "SessionStartedMessage",
    "SessionTerminatedMessage",
    "ArtifactDownloadCompletedMessage",
)

# Module-level registry for notification message types
_MESSAGE_TYPE_REGISTRY: dict[NotificationRuleType, type["NotifiableMessage"]] = {}


class NotifiableMessage(BaseModel):
    """Base class for all notification messages.

    All notification messages must inherit from this class and define
    their specific fields with comprehensive descriptions.
    """

    model_config = {"extra": "forbid"}  # Strict validation - reject unknown fields

    def __init_subclass__(cls):
        """Automatically register subclasses by their rule type."""
        try:
            rule_type = cls.rule_type()
            if rule_type in _MESSAGE_TYPE_REGISTRY:
                raise RuntimeError(f"Notification message type {rule_type} is already registered")
            _MESSAGE_TYPE_REGISTRY[rule_type] = cls
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
        model_class = _MESSAGE_TYPE_REGISTRY[rule_type]
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
        model_class = _MESSAGE_TYPE_REGISTRY[rule_type]
        return model_class.model_json_schema()


class SessionStartedMessage(NotifiableMessage):
    """Notification message for session start events.

    This message is sent when a compute session successfully starts.
    """

    @classmethod
    def rule_type(cls) -> NotificationRuleType:
        """Return the notification rule type for this message class."""
        return NotificationRuleType.SESSION_STARTED

    session_id: str = Field(description="Unique identifier of the compute session")
    session_name: Optional[str] = Field(
        default=None, description="User-defined name for the session, if provided"
    )
    session_type: str = Field(
        description="Type of session (e.g., 'interactive', 'batch', 'inference', 'system')"
    )
    cluster_mode: str = Field(
        description="Cluster mode of the session (e.g., 'single-node', 'multi-node')"
    )
    status: str = Field(description="Current status of the session")


class SessionTerminatedMessage(NotifiableMessage):
    """Notification message for session termination events.

    This message is sent when a compute session is terminated,
    either by user request or system action.
    """

    @classmethod
    def rule_type(cls) -> NotificationRuleType:
        """Return the notification rule type for this message class."""
        return NotificationRuleType.SESSION_TERMINATED

    session_id: str = Field(description="Unique identifier of the compute session")
    session_name: Optional[str] = Field(
        default=None, description="User-defined name for the session, if provided"
    )
    session_type: str = Field(
        description="Type of session (e.g., 'interactive', 'batch', 'inference', 'system')"
    )
    cluster_mode: str = Field(
        description="Cluster mode of the session (e.g., 'single-node', 'multi-node')"
    )
    status: str = Field(
        description="Final status of the session (e.g., 'terminated', 'cancelled', 'error')"
    )
    termination_reason: Optional[str] = Field(
        default=None,
        description="Reason for termination (e.g., 'user-requested', 'timeout', 'error')",
    )


class ArtifactDownloadCompletedMessage(NotifiableMessage):
    """Notification message for artifact download completion events.

    This message is sent when an artifact download operation completes.
    """

    @classmethod
    def rule_type(cls) -> NotificationRuleType:
        """Return the notification rule type for this message class."""
        return NotificationRuleType.ARTIFACT_DOWNLOAD_COMPLETED

    artifact_id: str = Field(description="Unique identifier of the artifact")
    artifact_name: str = Field(description="Name of the artifact")
    artifact_type: str = Field(description="Type of artifact (e.g., 'MODEL', 'PACKAGE', 'IMAGE')")
    registry_type: str = Field(
        description="Type of registry where the artifact is stored (e.g., 'HARBOR', 'HUGGINGFACE')"
    )
    registry_id: str = Field(description="Unique identifier of the registry")
    version: Optional[str] = Field(
        default=None, description="Version of the artifact revision, if available"
    )
    status: str = Field(description="Status of the artifact revision")
    success: bool = Field(description="Whether the download operation succeeded")
    digest: Optional[str] = Field(default=None, description="Digest of the artifact revision")
    verification_result: Optional[dict[str, Any]] = Field(
        default=None, description="Verification result of the artifact revision, if available"
    )
