"""Tests for ai.backend.common.dto.manager.v2.notification.request module."""

from __future__ import annotations

import uuid

import pytest
from pydantic import ValidationError

from ai.backend.common.api_handlers import SENTINEL, Sentinel
from ai.backend.common.data.notification.types import (
    EmailMessage,
    EmailSpec,
    NotificationChannelType,
    NotificationRuleType,
    SMTPConnection,
    WebhookSpec,
)
from ai.backend.common.dto.manager.v2.notification.request import (
    CreateNotificationChannelInput,
    CreateNotificationRuleInput,
    DeleteNotificationChannelInput,
    DeleteNotificationRuleInput,
    UpdateNotificationChannelInput,
    UpdateNotificationRuleInput,
    ValidateNotificationChannelInput,
    ValidateNotificationRuleInput,
)


def _make_webhook_spec() -> WebhookSpec:
    return WebhookSpec(url="https://example.com/webhook")


def _make_email_spec() -> EmailSpec:
    return EmailSpec(
        smtp=SMTPConnection(host="smtp.example.com", port=587),
        message=EmailMessage(
            from_email="noreply@example.com",
            to_emails=["admin@example.com"],
        ),
    )


class TestCreateNotificationChannelInput:
    """Tests for CreateNotificationChannelInput model creation and validation."""

    def test_valid_creation_with_webhook(self) -> None:
        inp = CreateNotificationChannelInput(
            name="My Webhook",
            channel_type=NotificationChannelType.WEBHOOK,
            spec=_make_webhook_spec(),
        )
        assert inp.name == "My Webhook"
        assert inp.channel_type == NotificationChannelType.WEBHOOK
        assert inp.enabled is True

    def test_valid_creation_with_email(self) -> None:
        inp = CreateNotificationChannelInput(
            name="Email Channel",
            channel_type=NotificationChannelType.EMAIL,
            spec=_make_email_spec(),
        )
        assert inp.name == "Email Channel"
        assert inp.channel_type == NotificationChannelType.EMAIL

    def test_default_enabled_is_true(self) -> None:
        inp = CreateNotificationChannelInput(
            name="Channel",
            channel_type=NotificationChannelType.WEBHOOK,
            spec=_make_webhook_spec(),
        )
        assert inp.enabled is True

    def test_enabled_can_be_false(self) -> None:
        inp = CreateNotificationChannelInput(
            name="Disabled",
            channel_type=NotificationChannelType.WEBHOOK,
            spec=_make_webhook_spec(),
            enabled=False,
        )
        assert inp.enabled is False

    def test_default_description_is_none(self) -> None:
        inp = CreateNotificationChannelInput(
            name="Channel",
            channel_type=NotificationChannelType.WEBHOOK,
            spec=_make_webhook_spec(),
        )
        assert inp.description is None

    def test_description_can_be_set(self) -> None:
        inp = CreateNotificationChannelInput(
            name="Channel",
            description="My channel",
            channel_type=NotificationChannelType.WEBHOOK,
            spec=_make_webhook_spec(),
        )
        assert inp.description == "My channel"

    def test_name_whitespace_is_stripped(self) -> None:
        inp = CreateNotificationChannelInput(
            name="  My Webhook  ",
            channel_type=NotificationChannelType.WEBHOOK,
            spec=_make_webhook_spec(),
        )
        assert inp.name == "My Webhook"

    def test_name_leading_whitespace_stripped(self) -> None:
        inp = CreateNotificationChannelInput(
            name="  Channel",
            channel_type=NotificationChannelType.WEBHOOK,
            spec=_make_webhook_spec(),
        )
        assert inp.name == "Channel"

    def test_name_at_max_length_is_valid(self) -> None:
        inp = CreateNotificationChannelInput(
            name="a" * 256,
            channel_type=NotificationChannelType.WEBHOOK,
            spec=_make_webhook_spec(),
        )
        assert len(inp.name) == 256


class TestCreateNotificationChannelInputValidationFailures:
    """Tests for CreateNotificationChannelInput validation failures."""

    def test_empty_name_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            CreateNotificationChannelInput(
                name="",
                channel_type=NotificationChannelType.WEBHOOK,
                spec=_make_webhook_spec(),
            )

    def test_whitespace_only_name_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            CreateNotificationChannelInput(
                name="   ",
                channel_type=NotificationChannelType.WEBHOOK,
                spec=_make_webhook_spec(),
            )

    def test_tab_only_name_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            CreateNotificationChannelInput(
                name="\t",
                channel_type=NotificationChannelType.WEBHOOK,
                spec=_make_webhook_spec(),
            )

    def test_name_exceeding_max_length_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            CreateNotificationChannelInput(
                name="a" * 257,
                channel_type=NotificationChannelType.WEBHOOK,
                spec=_make_webhook_spec(),
            )

    def test_missing_name_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            CreateNotificationChannelInput.model_validate({
                "channel_type": "webhook",
                "spec": {"url": "https://example.com"},
            })


class TestUpdateNotificationChannelInput:
    """Tests for UpdateNotificationChannelInput model."""

    def test_default_description_is_sentinel(self) -> None:
        inp = UpdateNotificationChannelInput()
        assert inp.description is SENTINEL
        assert isinstance(inp.description, Sentinel)

    def test_explicit_sentinel_description(self) -> None:
        inp = UpdateNotificationChannelInput(description=SENTINEL)
        assert inp.description is SENTINEL

    def test_none_description_means_no_change(self) -> None:
        inp = UpdateNotificationChannelInput(description=None)
        assert inp.description is None

    def test_string_description_update(self) -> None:
        inp = UpdateNotificationChannelInput(description="New desc")
        assert inp.description == "New desc"

    def test_default_name_is_none(self) -> None:
        inp = UpdateNotificationChannelInput()
        assert inp.name is None

    def test_name_whitespace_stripped(self) -> None:
        inp = UpdateNotificationChannelInput(name="  Updated  ")
        assert inp.name == "Updated"

    def test_whitespace_only_name_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            UpdateNotificationChannelInput(name="   ")

    def test_empty_name_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            UpdateNotificationChannelInput(name="")

    def test_default_enabled_is_none(self) -> None:
        inp = UpdateNotificationChannelInput()
        assert inp.enabled is None

    def test_enabled_update(self) -> None:
        inp = UpdateNotificationChannelInput(enabled=False)
        assert inp.enabled is False

    def test_spec_update_with_webhook(self) -> None:
        inp = UpdateNotificationChannelInput(spec=_make_webhook_spec())
        assert inp.spec is not None

    def test_spec_default_is_none(self) -> None:
        inp = UpdateNotificationChannelInput()
        assert inp.spec is None

    def test_all_fields_none_is_valid(self) -> None:
        inp = UpdateNotificationChannelInput(name=None, description=None, spec=None, enabled=None)
        assert inp.name is None
        assert inp.description is None
        assert inp.spec is None
        assert inp.enabled is None


class TestDeleteNotificationChannelInput:
    """Tests for DeleteNotificationChannelInput model."""

    def test_valid_creation_with_uuid(self) -> None:
        channel_id = uuid.uuid4()
        inp = DeleteNotificationChannelInput(id=channel_id)
        assert inp.id == channel_id

    def test_valid_creation_from_uuid_string(self) -> None:
        channel_id = uuid.uuid4()
        inp = DeleteNotificationChannelInput.model_validate({"id": str(channel_id)})
        assert inp.id == channel_id

    def test_invalid_uuid_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            DeleteNotificationChannelInput.model_validate({"id": "not-a-uuid"})

    def test_missing_id_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            DeleteNotificationChannelInput.model_validate({})

    def test_id_is_uuid_instance(self) -> None:
        channel_id = uuid.uuid4()
        inp = DeleteNotificationChannelInput(id=channel_id)
        assert isinstance(inp.id, uuid.UUID)


class TestCreateNotificationRuleInput:
    """Tests for CreateNotificationRuleInput model."""

    def test_valid_creation(self) -> None:
        channel_id = uuid.uuid4()
        inp = CreateNotificationRuleInput(
            name="Session Alert",
            rule_type=NotificationRuleType.SESSION_STARTED,
            channel_id=channel_id,
            message_template="Session {{ session_id }} started",
        )
        assert inp.name == "Session Alert"
        assert inp.rule_type == NotificationRuleType.SESSION_STARTED
        assert inp.channel_id == channel_id
        assert inp.enabled is True

    def test_default_enabled_is_true(self) -> None:
        channel_id = uuid.uuid4()
        inp = CreateNotificationRuleInput(
            name="Rule",
            rule_type=NotificationRuleType.SESSION_TERMINATED,
            channel_id=channel_id,
            message_template="template",
        )
        assert inp.enabled is True

    def test_default_description_is_none(self) -> None:
        channel_id = uuid.uuid4()
        inp = CreateNotificationRuleInput(
            name="Rule",
            rule_type=NotificationRuleType.SESSION_TERMINATED,
            channel_id=channel_id,
            message_template="template",
        )
        assert inp.description is None

    def test_name_whitespace_stripped(self) -> None:
        channel_id = uuid.uuid4()
        inp = CreateNotificationRuleInput(
            name="  Alert Rule  ",
            rule_type=NotificationRuleType.SESSION_STARTED,
            channel_id=channel_id,
            message_template="template",
        )
        assert inp.name == "Alert Rule"

    def test_empty_name_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            CreateNotificationRuleInput(
                name="",
                rule_type=NotificationRuleType.SESSION_STARTED,
                channel_id=uuid.uuid4(),
                message_template="template",
            )

    def test_whitespace_only_name_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            CreateNotificationRuleInput(
                name="   ",
                rule_type=NotificationRuleType.SESSION_STARTED,
                channel_id=uuid.uuid4(),
                message_template="template",
            )

    def test_message_template_at_max_length_is_valid(self) -> None:
        channel_id = uuid.uuid4()
        inp = CreateNotificationRuleInput(
            name="Rule",
            rule_type=NotificationRuleType.SESSION_STARTED,
            channel_id=channel_id,
            message_template="x" * 65536,
        )
        assert len(inp.message_template) == 65536

    def test_message_template_exceeding_max_length_raises_error(self) -> None:
        with pytest.raises(ValidationError):
            CreateNotificationRuleInput(
                name="Rule",
                rule_type=NotificationRuleType.SESSION_STARTED,
                channel_id=uuid.uuid4(),
                message_template="x" * 65537,
            )


class TestUpdateNotificationRuleInput:
    """Tests for UpdateNotificationRuleInput model."""

    def test_default_description_is_sentinel(self) -> None:
        inp = UpdateNotificationRuleInput()
        assert inp.description is SENTINEL
        assert isinstance(inp.description, Sentinel)

    def test_explicit_sentinel_description(self) -> None:
        inp = UpdateNotificationRuleInput(description=SENTINEL)
        assert inp.description is SENTINEL

    def test_none_description_means_no_change(self) -> None:
        inp = UpdateNotificationRuleInput(description=None)
        assert inp.description is None

    def test_default_name_is_none(self) -> None:
        inp = UpdateNotificationRuleInput()
        assert inp.name is None

    def test_name_whitespace_stripped(self) -> None:
        inp = UpdateNotificationRuleInput(name="  Updated Rule  ")
        assert inp.name == "Updated Rule"

    def test_whitespace_only_name_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            UpdateNotificationRuleInput(name="   ")

    def test_default_message_template_is_none(self) -> None:
        inp = UpdateNotificationRuleInput()
        assert inp.message_template is None

    def test_message_template_update(self) -> None:
        inp = UpdateNotificationRuleInput(message_template="New template")
        assert inp.message_template == "New template"

    def test_default_enabled_is_none(self) -> None:
        inp = UpdateNotificationRuleInput()
        assert inp.enabled is None

    def test_enabled_update(self) -> None:
        inp = UpdateNotificationRuleInput(enabled=True)
        assert inp.enabled is True

    def test_all_none_fields_is_valid(self) -> None:
        inp = UpdateNotificationRuleInput(
            name=None, description=None, message_template=None, enabled=None
        )
        assert inp.name is None
        assert inp.description is None
        assert inp.message_template is None
        assert inp.enabled is None


class TestDeleteNotificationRuleInput:
    """Tests for DeleteNotificationRuleInput model."""

    def test_valid_creation_with_uuid(self) -> None:
        rule_id = uuid.uuid4()
        inp = DeleteNotificationRuleInput(id=rule_id)
        assert inp.id == rule_id

    def test_valid_creation_from_uuid_string(self) -> None:
        rule_id = uuid.uuid4()
        inp = DeleteNotificationRuleInput.model_validate({"id": str(rule_id)})
        assert inp.id == rule_id

    def test_invalid_uuid_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            DeleteNotificationRuleInput.model_validate({"id": "not-a-uuid"})

    def test_missing_id_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            DeleteNotificationRuleInput.model_validate({})

    def test_id_is_uuid_instance(self) -> None:
        rule_id = uuid.uuid4()
        inp = DeleteNotificationRuleInput(id=rule_id)
        assert isinstance(inp.id, uuid.UUID)


class TestValidateNotificationChannelInput:
    """Tests for ValidateNotificationChannelInput model."""

    def test_valid_creation(self) -> None:
        channel_id = uuid.uuid4()
        inp = ValidateNotificationChannelInput(id=channel_id, test_message="Hello, World!")
        assert inp.test_message == "Hello, World!"
        assert inp.id == channel_id

    def test_empty_test_message_is_valid(self) -> None:
        inp = ValidateNotificationChannelInput(id=uuid.uuid4(), test_message="")
        assert inp.test_message == ""

    def test_test_message_at_max_length_is_valid(self) -> None:
        inp = ValidateNotificationChannelInput(id=uuid.uuid4(), test_message="x" * 5000)
        assert len(inp.test_message) == 5000

    def test_test_message_exceeding_max_length_raises_error(self) -> None:
        with pytest.raises(ValidationError):
            ValidateNotificationChannelInput(id=uuid.uuid4(), test_message="x" * 5001)

    def test_missing_test_message_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            ValidateNotificationChannelInput.model_validate({})


class TestValidateNotificationRuleInput:
    """Tests for ValidateNotificationRuleInput model."""

    def test_default_notification_data_is_empty_dict(self) -> None:
        rule_id = uuid.uuid4()
        inp = ValidateNotificationRuleInput(id=rule_id)
        assert inp.notification_data == {}

    def test_notification_data_can_be_set(self) -> None:
        inp = ValidateNotificationRuleInput(
            id=uuid.uuid4(),
            notification_data={"session_id": "abc123", "user": "admin"},
        )
        assert inp.notification_data["session_id"] == "abc123"
        assert inp.notification_data["user"] == "admin"

    def test_notification_data_from_dict(self) -> None:
        rule_id = uuid.uuid4()
        inp = ValidateNotificationRuleInput.model_validate({
            "id": str(rule_id),
            "notification_data": {"key": "value"},
        })
        assert inp.notification_data["key"] == "value"

    def test_round_trip_serialization(self) -> None:
        inp = ValidateNotificationRuleInput(
            id=uuid.uuid4(),
            notification_data={"event": "session.started", "count": 5},
        )
        json_str = inp.model_dump_json()
        restored = ValidateNotificationRuleInput.model_validate_json(json_str)
        assert restored.notification_data["event"] == "session.started"
        assert restored.notification_data["count"] == 5
