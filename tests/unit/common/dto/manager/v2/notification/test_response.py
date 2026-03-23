"""Tests for ai.backend.common.dto.manager.v2.notification.response module."""

from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from ai.backend.common.dto.manager.v2.notification.response import (
    CreateNotificationChannelPayload,
    CreateNotificationRulePayload,
    DeleteNotificationChannelPayload,
    DeleteNotificationRulePayload,
    NotificationChannelNode,
    NotificationRuleNode,
    UpdateNotificationChannelPayload,
    UpdateNotificationRulePayload,
    ValidateNotificationChannelPayload,
    ValidateNotificationRulePayload,
)
from ai.backend.common.dto.manager.v2.notification.types import (
    EmailMessageInfo,
    EmailSpecInfo,
    NotificationChannelTypeDTO,
    NotificationRuleTypeDTO,
    SMTPConnectionInfo,
    WebhookSpecInfo,
)


def _make_webhook_spec_info() -> WebhookSpecInfo:
    return WebhookSpecInfo(
        channel_type=NotificationChannelTypeDTO.WEBHOOK,
        url="https://example.com/webhook",
    )


def _make_email_spec_info() -> EmailSpecInfo:
    return EmailSpecInfo(
        channel_type=NotificationChannelTypeDTO.EMAIL,
        smtp=SMTPConnectionInfo(
            host="smtp.example.com",
            port=587,
            use_tls=True,
            timeout=30,
        ),
        message=EmailMessageInfo(
            from_email="noreply@example.com",
            to_emails=["admin@example.com"],
        ),
    )


def _make_channel_node(
    spec: WebhookSpecInfo | EmailSpecInfo | None = None,
    channel_type: NotificationChannelTypeDTO = NotificationChannelTypeDTO.WEBHOOK,
) -> NotificationChannelNode:
    now = datetime.now(tz=UTC)
    return NotificationChannelNode(
        id=uuid.uuid4(),
        name="Test Channel",
        channel_type=channel_type,
        spec=spec or _make_webhook_spec_info(),
        enabled=True,
        created_at=now,
        created_by=uuid.uuid4(),
        updated_at=now,
    )


class TestNotificationChannelNodeCreation:
    """Tests for NotificationChannelNode model creation."""

    def test_creation_with_webhook_spec(self) -> None:
        channel_id = uuid.uuid4()
        creator_id = uuid.uuid4()
        now = datetime.now(tz=UTC)
        node = NotificationChannelNode(
            id=channel_id,
            name="Webhook Channel",
            description="A webhook channel",
            channel_type=NotificationChannelTypeDTO.WEBHOOK,
            spec=_make_webhook_spec_info(),
            enabled=True,
            created_at=now,
            created_by=creator_id,
            updated_at=now,
        )
        assert node.id == channel_id
        assert node.name == "Webhook Channel"
        assert node.description == "A webhook channel"
        assert node.channel_type == NotificationChannelTypeDTO.WEBHOOK
        assert node.enabled is True
        assert node.created_by == creator_id

    def test_creation_with_email_spec(self) -> None:
        now = datetime.now(tz=UTC)
        node = NotificationChannelNode(
            id=uuid.uuid4(),
            name="Email Channel",
            channel_type=NotificationChannelTypeDTO.EMAIL,
            spec=_make_email_spec_info(),
            enabled=True,
            created_at=now,
            created_by=uuid.uuid4(),
            updated_at=now,
        )
        assert node.channel_type == NotificationChannelTypeDTO.EMAIL
        assert isinstance(node.spec, EmailSpecInfo)

    def test_description_defaults_to_none(self) -> None:
        node = _make_channel_node()
        assert node.description is None

    def test_explicit_description_none(self) -> None:
        now = datetime.now(tz=UTC)
        node = NotificationChannelNode(
            id=uuid.uuid4(),
            name="Channel",
            description=None,
            channel_type=NotificationChannelTypeDTO.WEBHOOK,
            spec=_make_webhook_spec_info(),
            enabled=True,
            created_at=now,
            created_by=uuid.uuid4(),
            updated_at=now,
        )
        assert node.description is None

    def test_spec_webhook_url_accessible(self) -> None:
        spec = WebhookSpecInfo(
            channel_type=NotificationChannelTypeDTO.WEBHOOK,
            url="https://hooks.example.com",
        )
        node = _make_channel_node(spec=spec)
        assert isinstance(node.spec, WebhookSpecInfo)
        assert node.spec.url == "https://hooks.example.com"

    def test_spec_email_fields_accessible(self) -> None:
        node = _make_channel_node(
            spec=_make_email_spec_info(),
            channel_type=NotificationChannelTypeDTO.EMAIL,
        )
        assert isinstance(node.spec, EmailSpecInfo)
        assert node.spec.smtp.host == "smtp.example.com"


class TestNotificationChannelNodeSerialization:
    """Tests for NotificationChannelNode serialization."""

    def test_model_dump_json_includes_all_fields(self) -> None:
        node = _make_channel_node()
        data = json.loads(node.model_dump_json())
        assert "id" in data
        assert "name" in data
        assert "channel_type" in data
        assert "spec" in data
        assert "enabled" in data
        assert "created_at" in data
        assert "created_by" in data
        assert "updated_at" in data

    def test_round_trip_with_webhook_spec(self) -> None:
        node = _make_channel_node()
        json_str = node.model_dump_json()
        restored = NotificationChannelNode.model_validate_json(json_str)
        assert restored.id == node.id
        assert restored.name == node.name
        assert restored.channel_type == node.channel_type
        assert restored.enabled == node.enabled

    def test_round_trip_with_email_spec(self) -> None:
        node = _make_channel_node(
            spec=_make_email_spec_info(),
            channel_type=NotificationChannelTypeDTO.EMAIL,
        )
        json_str = node.model_dump_json()
        restored = NotificationChannelNode.model_validate_json(json_str)
        assert restored.id == node.id
        assert restored.channel_type == NotificationChannelTypeDTO.EMAIL

    def test_nested_spec_preserved_in_round_trip(self) -> None:
        spec = WebhookSpecInfo(
            channel_type=NotificationChannelTypeDTO.WEBHOOK,
            url="https://test.example.com/hook",
        )
        node = _make_channel_node(spec=spec)
        json_str = node.model_dump_json()
        restored = NotificationChannelNode.model_validate_json(json_str)
        assert isinstance(restored.spec, WebhookSpecInfo)
        assert restored.spec.url == "https://test.example.com/hook"


class TestNotificationRuleNodeCreation:
    """Tests for NotificationRuleNode model creation."""

    def test_creation_with_embedded_channel_node(self) -> None:
        rule_id = uuid.uuid4()
        creator_id = uuid.uuid4()
        now = datetime.now(tz=UTC)
        channel_node = _make_channel_node()
        node = NotificationRuleNode(
            id=rule_id,
            name="Session Alert Rule",
            description="Alert on session events",
            rule_type=NotificationRuleTypeDTO.SESSION_STARTED,
            channel=channel_node,
            message_template="Session {{ session_id }} started",
            enabled=True,
            created_at=now,
            created_by=creator_id,
            updated_at=now,
        )
        assert node.id == rule_id
        assert node.name == "Session Alert Rule"
        assert node.rule_type == NotificationRuleTypeDTO.SESSION_STARTED
        assert node.channel.name == "Test Channel"
        assert node.enabled is True

    def test_description_defaults_to_none(self) -> None:
        now = datetime.now(tz=UTC)
        node = NotificationRuleNode(
            id=uuid.uuid4(),
            name="Rule",
            rule_type=NotificationRuleTypeDTO.SESSION_TERMINATED,
            channel=_make_channel_node(),
            message_template="template",
            enabled=True,
            created_at=now,
            created_by=uuid.uuid4(),
            updated_at=now,
        )
        assert node.description is None

    def test_embedded_channel_node_accessible(self) -> None:
        channel_node = _make_channel_node()
        now = datetime.now(tz=UTC)
        rule_node = NotificationRuleNode(
            id=uuid.uuid4(),
            name="Rule",
            rule_type=NotificationRuleTypeDTO.SESSION_STARTED,
            channel=channel_node,
            message_template="template",
            enabled=True,
            created_at=now,
            created_by=uuid.uuid4(),
            updated_at=now,
        )
        assert rule_node.channel.id == channel_node.id
        assert rule_node.channel.channel_type == NotificationChannelTypeDTO.WEBHOOK

    def test_rule_type_artifact_download(self) -> None:
        now = datetime.now(tz=UTC)
        node = NotificationRuleNode(
            id=uuid.uuid4(),
            name="Download Alert",
            rule_type=NotificationRuleTypeDTO.ARTIFACT_DOWNLOAD_COMPLETED,
            channel=_make_channel_node(),
            message_template="Download done",
            enabled=True,
            created_at=now,
            created_by=uuid.uuid4(),
            updated_at=now,
        )
        assert node.rule_type == NotificationRuleTypeDTO.ARTIFACT_DOWNLOAD_COMPLETED


class TestNotificationRuleNodeSerialization:
    """Tests for NotificationRuleNode serialization with nested channel."""

    def test_round_trip_preserves_nested_channel(self) -> None:
        channel_node = _make_channel_node()
        now = datetime.now(tz=UTC)
        rule_node = NotificationRuleNode(
            id=uuid.uuid4(),
            name="Alert Rule",
            rule_type=NotificationRuleTypeDTO.SESSION_STARTED,
            channel=channel_node,
            message_template="{{ session_id }} started",
            enabled=True,
            created_at=now,
            created_by=uuid.uuid4(),
            updated_at=now,
        )
        json_str = rule_node.model_dump_json()
        restored = NotificationRuleNode.model_validate_json(json_str)
        assert restored.id == rule_node.id
        assert restored.channel.id == channel_node.id
        assert restored.channel.name == "Test Channel"

    def test_nested_channel_spec_preserved_in_json(self) -> None:
        channel_node = _make_channel_node()
        now = datetime.now(tz=UTC)
        rule_node = NotificationRuleNode(
            id=uuid.uuid4(),
            name="Rule",
            rule_type=NotificationRuleTypeDTO.SESSION_TERMINATED,
            channel=channel_node,
            message_template="template",
            enabled=True,
            created_at=now,
            created_by=uuid.uuid4(),
            updated_at=now,
        )
        data = json.loads(rule_node.model_dump_json())
        assert "channel" in data
        assert "spec" in data["channel"]
        assert "url" in data["channel"]["spec"]


class TestCreateNotificationChannelPayload:
    """Tests for CreateNotificationChannelPayload model."""

    def test_creation_with_channel_node(self) -> None:
        node = _make_channel_node()
        payload = CreateNotificationChannelPayload(channel=node)
        assert payload.channel.name == "Test Channel"
        assert payload.channel.id == node.id

    def test_round_trip_serialization(self) -> None:
        node = _make_channel_node()
        payload = CreateNotificationChannelPayload(channel=node)
        json_str = payload.model_dump_json()
        restored = CreateNotificationChannelPayload.model_validate_json(json_str)
        assert restored.channel.id == node.id
        assert restored.channel.name == node.name


class TestUpdateNotificationChannelPayload:
    """Tests for UpdateNotificationChannelPayload model."""

    def test_creation_with_channel_node(self) -> None:
        now = datetime.now(tz=UTC)
        node = NotificationChannelNode(
            id=uuid.uuid4(),
            name="Updated Channel",
            channel_type=NotificationChannelTypeDTO.WEBHOOK,
            spec=_make_webhook_spec_info(),
            enabled=False,
            created_at=now,
            created_by=uuid.uuid4(),
            updated_at=now,
        )
        payload = UpdateNotificationChannelPayload(channel=node)
        assert payload.channel.name == "Updated Channel"
        assert payload.channel.enabled is False

    def test_round_trip_serialization(self) -> None:
        node = _make_channel_node()
        payload = UpdateNotificationChannelPayload(channel=node)
        json_str = payload.model_dump_json()
        restored = UpdateNotificationChannelPayload.model_validate_json(json_str)
        assert restored.channel.id == node.id


class TestDeleteNotificationChannelPayload:
    """Tests for DeleteNotificationChannelPayload model."""

    def test_creation_with_uuid(self) -> None:
        channel_id = uuid.uuid4()
        payload = DeleteNotificationChannelPayload(id=channel_id)
        assert payload.id == channel_id

    def test_id_is_uuid_instance(self) -> None:
        channel_id = uuid.uuid4()
        payload = DeleteNotificationChannelPayload(id=channel_id)
        assert isinstance(payload.id, uuid.UUID)

    def test_creation_from_uuid_string(self) -> None:
        channel_id = uuid.uuid4()
        payload = DeleteNotificationChannelPayload.model_validate({"id": str(channel_id)})
        assert payload.id == channel_id

    def test_round_trip_serialization(self) -> None:
        channel_id = uuid.uuid4()
        payload = DeleteNotificationChannelPayload(id=channel_id)
        json_str = payload.model_dump_json()
        restored = DeleteNotificationChannelPayload.model_validate_json(json_str)
        assert restored.id == channel_id


class TestCreateNotificationRulePayload:
    """Tests for CreateNotificationRulePayload model."""

    def _make_rule_node(self) -> NotificationRuleNode:
        now = datetime.now(tz=UTC)
        return NotificationRuleNode(
            id=uuid.uuid4(),
            name="Alert Rule",
            rule_type=NotificationRuleTypeDTO.SESSION_STARTED,
            channel=_make_channel_node(),
            message_template="template",
            enabled=True,
            created_at=now,
            created_by=uuid.uuid4(),
            updated_at=now,
        )

    def test_creation_with_rule_node(self) -> None:
        rule_node = self._make_rule_node()
        payload = CreateNotificationRulePayload(rule=rule_node)
        assert payload.rule.name == "Alert Rule"
        assert payload.rule.id == rule_node.id

    def test_round_trip_serialization(self) -> None:
        rule_node = self._make_rule_node()
        payload = CreateNotificationRulePayload(rule=rule_node)
        json_str = payload.model_dump_json()
        restored = CreateNotificationRulePayload.model_validate_json(json_str)
        assert restored.rule.id == rule_node.id
        assert restored.rule.channel.name == "Test Channel"


class TestUpdateNotificationRulePayload:
    """Tests for UpdateNotificationRulePayload model."""

    def test_creation_with_rule_node(self) -> None:
        now = datetime.now(tz=UTC)
        rule_node = NotificationRuleNode(
            id=uuid.uuid4(),
            name="Updated Rule",
            rule_type=NotificationRuleTypeDTO.SESSION_TERMINATED,
            channel=_make_channel_node(),
            message_template="updated template",
            enabled=False,
            created_at=now,
            created_by=uuid.uuid4(),
            updated_at=now,
        )
        payload = UpdateNotificationRulePayload(rule=rule_node)
        assert payload.rule.name == "Updated Rule"
        assert payload.rule.enabled is False

    def test_round_trip_serialization(self) -> None:
        now = datetime.now(tz=UTC)
        rule_node = NotificationRuleNode(
            id=uuid.uuid4(),
            name="Rule",
            rule_type=NotificationRuleTypeDTO.SESSION_STARTED,
            channel=_make_channel_node(),
            message_template="template",
            enabled=True,
            created_at=now,
            created_by=uuid.uuid4(),
            updated_at=now,
        )
        payload = UpdateNotificationRulePayload(rule=rule_node)
        json_str = payload.model_dump_json()
        restored = UpdateNotificationRulePayload.model_validate_json(json_str)
        assert restored.rule.id == rule_node.id


class TestDeleteNotificationRulePayload:
    """Tests for DeleteNotificationRulePayload model."""

    def test_creation_with_uuid(self) -> None:
        rule_id = uuid.uuid4()
        payload = DeleteNotificationRulePayload(id=rule_id)
        assert payload.id == rule_id

    def test_id_is_uuid_instance(self) -> None:
        rule_id = uuid.uuid4()
        payload = DeleteNotificationRulePayload(id=rule_id)
        assert isinstance(payload.id, uuid.UUID)

    def test_creation_from_uuid_string(self) -> None:
        rule_id = uuid.uuid4()
        payload = DeleteNotificationRulePayload.model_validate({"id": str(rule_id)})
        assert payload.id == rule_id

    def test_round_trip_serialization(self) -> None:
        rule_id = uuid.uuid4()
        payload = DeleteNotificationRulePayload(id=rule_id)
        json_str = payload.model_dump_json()
        restored = DeleteNotificationRulePayload.model_validate_json(json_str)
        assert restored.id == rule_id


class TestValidateNotificationChannelPayload:
    """Tests for ValidateNotificationChannelPayload model."""

    def test_creation_with_id(self) -> None:
        channel_id = uuid.uuid4()
        payload = ValidateNotificationChannelPayload(id=channel_id)
        assert payload.id == channel_id

    def test_id_is_uuid_instance(self) -> None:
        channel_id = uuid.uuid4()
        payload = ValidateNotificationChannelPayload(id=channel_id)
        assert isinstance(payload.id, uuid.UUID)

    def test_creation_from_uuid_string(self) -> None:
        channel_id = uuid.uuid4()
        payload = ValidateNotificationChannelPayload.model_validate({"id": str(channel_id)})
        assert payload.id == channel_id

    def test_round_trip_serialization(self) -> None:
        channel_id = uuid.uuid4()
        payload = ValidateNotificationChannelPayload(id=channel_id)
        json_str = payload.model_dump_json()
        restored = ValidateNotificationChannelPayload.model_validate_json(json_str)
        assert restored.id == channel_id


class TestValidateNotificationRulePayload:
    """Tests for ValidateNotificationRulePayload model."""

    def test_creation_with_message(self) -> None:
        payload = ValidateNotificationRulePayload(message="Session abc123 has started.")
        assert payload.message == "Session abc123 has started."

    def test_empty_message_is_valid(self) -> None:
        payload = ValidateNotificationRulePayload(message="")
        assert payload.message == ""

    def test_round_trip_serialization(self) -> None:
        payload = ValidateNotificationRulePayload(message="Rendered: hello world")
        json_str = payload.model_dump_json()
        restored = ValidateNotificationRulePayload.model_validate_json(json_str)
        assert restored.message == "Rendered: hello world"

    def test_missing_message_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            ValidateNotificationRulePayload.model_validate({})
