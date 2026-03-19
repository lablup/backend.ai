"""Tests for ai.backend.common.dto.manager.v2.notification.types module."""

from __future__ import annotations

import json

from ai.backend.common.data.notification.types import (
    NotificationChannelType,
    NotificationRuleType,
)
from ai.backend.common.dto.manager.v2.notification.types import (
    EmailSpecInfo,
    NotificationChannelOrderField,
    NotificationRuleOrderField,
    OrderDirection,
    WebhookSpecInfo,
)
from ai.backend.common.dto.manager.v2.notification.types import (
    NotificationChannelType as ExportedNotificationChannelType,
)
from ai.backend.common.dto.manager.v2.notification.types import (
    NotificationRuleType as ExportedNotificationRuleType,
)


class TestOrderDirection:
    """Tests for OrderDirection enum."""

    def test_asc_value(self) -> None:
        assert OrderDirection.ASC.value == "asc"

    def test_desc_value(self) -> None:
        assert OrderDirection.DESC.value == "desc"

    def test_all_values_are_strings(self) -> None:
        for member in OrderDirection:
            assert isinstance(member.value, str)

    def test_enum_members_count(self) -> None:
        members = list(OrderDirection)
        assert len(members) == 2

    def test_from_string_asc(self) -> None:
        assert OrderDirection("asc") is OrderDirection.ASC

    def test_from_string_desc(self) -> None:
        assert OrderDirection("desc") is OrderDirection.DESC


class TestNotificationChannelOrderField:
    """Tests for NotificationChannelOrderField enum."""

    def test_name_value(self) -> None:
        assert NotificationChannelOrderField.NAME.value == "name"

    def test_created_at_value(self) -> None:
        assert NotificationChannelOrderField.CREATED_AT.value == "created_at"

    def test_updated_at_value(self) -> None:
        assert NotificationChannelOrderField.UPDATED_AT.value == "updated_at"

    def test_all_values_are_strings(self) -> None:
        for member in NotificationChannelOrderField:
            assert isinstance(member.value, str)

    def test_enum_members_count(self) -> None:
        members = list(NotificationChannelOrderField)
        assert len(members) == 3

    def test_from_string_name(self) -> None:
        assert NotificationChannelOrderField("name") is NotificationChannelOrderField.NAME

    def test_from_string_created_at(self) -> None:
        assert (
            NotificationChannelOrderField("created_at") is NotificationChannelOrderField.CREATED_AT
        )

    def test_from_string_updated_at(self) -> None:
        assert (
            NotificationChannelOrderField("updated_at") is NotificationChannelOrderField.UPDATED_AT
        )


class TestNotificationRuleOrderField:
    """Tests for NotificationRuleOrderField enum."""

    def test_name_value(self) -> None:
        assert NotificationRuleOrderField.NAME.value == "name"

    def test_created_at_value(self) -> None:
        assert NotificationRuleOrderField.CREATED_AT.value == "created_at"

    def test_updated_at_value(self) -> None:
        assert NotificationRuleOrderField.UPDATED_AT.value == "updated_at"

    def test_all_values_are_strings(self) -> None:
        for member in NotificationRuleOrderField:
            assert isinstance(member.value, str)

    def test_enum_members_count(self) -> None:
        members = list(NotificationRuleOrderField)
        assert len(members) == 3

    def test_from_string_name(self) -> None:
        assert NotificationRuleOrderField("name") is NotificationRuleOrderField.NAME

    def test_from_string_created_at(self) -> None:
        assert NotificationRuleOrderField("created_at") is NotificationRuleOrderField.CREATED_AT


class TestReExportedEnums:
    """Tests verifying that enums are properly re-exported from types module."""

    def test_notification_channel_type_is_same_object(self) -> None:
        assert ExportedNotificationChannelType is NotificationChannelType

    def test_notification_rule_type_is_same_object(self) -> None:
        assert ExportedNotificationRuleType is NotificationRuleType

    def test_channel_type_webhook_value(self) -> None:
        assert ExportedNotificationChannelType.WEBHOOK.value == "webhook"

    def test_channel_type_email_value(self) -> None:
        assert ExportedNotificationChannelType.EMAIL.value == "email"

    def test_rule_type_session_started_value(self) -> None:
        assert ExportedNotificationRuleType.SESSION_STARTED.value == "session.started"

    def test_rule_type_session_terminated_value(self) -> None:
        assert ExportedNotificationRuleType.SESSION_TERMINATED.value == "session.terminated"

    def test_rule_type_artifact_download_completed_value(self) -> None:
        assert (
            ExportedNotificationRuleType.ARTIFACT_DOWNLOAD_COMPLETED.value
            == "artifact.download.completed"
        )

    def test_rule_type_endpoint_lifecycle_changed_value(self) -> None:
        assert (
            ExportedNotificationRuleType.ENDPOINT_LIFECYCLE_CHANGED.value
            == "endpoint.lifecycle.changed"
        )


class TestWebhookSpecInfo:
    """Tests for WebhookSpecInfo response sub-model."""

    def test_creation_with_url(self) -> None:
        info = WebhookSpecInfo(url="https://example.com/webhook")
        assert info.url == "https://example.com/webhook"

    def test_creation_from_dict(self) -> None:
        info = WebhookSpecInfo.model_validate({"url": "https://hooks.example.com"})
        assert info.url == "https://hooks.example.com"

    def test_model_dump_json(self) -> None:
        info = WebhookSpecInfo(url="https://example.com/hook")
        parsed = json.loads(info.model_dump_json())
        assert parsed["url"] == "https://example.com/hook"

    def test_round_trip_serialization(self) -> None:
        info = WebhookSpecInfo(url="https://example.com/hook")
        json_str = info.model_dump_json()
        restored = WebhookSpecInfo.model_validate_json(json_str)
        assert restored.url == info.url


class TestEmailSpecInfo:
    """Tests for EmailSpecInfo response sub-model."""

    def test_creation_with_all_fields(self) -> None:
        info = EmailSpecInfo(
            smtp_host="smtp.example.com",
            smtp_port=587,
            smtp_use_tls=True,
            smtp_timeout=30,
            from_email="noreply@example.com",
            to_emails=["admin@example.com", "ops@example.com"],
        )
        assert info.smtp_host == "smtp.example.com"
        assert info.smtp_port == 587
        assert info.smtp_use_tls is True
        assert info.smtp_timeout == 30
        assert info.from_email == "noreply@example.com"
        assert info.to_emails == ["admin@example.com", "ops@example.com"]

    def test_creation_from_dict(self) -> None:
        info = EmailSpecInfo.model_validate({
            "smtp_host": "mail.example.com",
            "smtp_port": 465,
            "smtp_use_tls": False,
            "smtp_timeout": 60,
            "from_email": "sender@example.com",
            "to_emails": ["recipient@example.com"],
        })
        assert info.smtp_host == "mail.example.com"
        assert info.smtp_port == 465

    def test_round_trip_serialization(self) -> None:
        info = EmailSpecInfo(
            smtp_host="smtp.example.com",
            smtp_port=587,
            smtp_use_tls=True,
            smtp_timeout=30,
            from_email="noreply@example.com",
            to_emails=["admin@example.com"],
        )
        json_str = info.model_dump_json()
        restored = EmailSpecInfo.model_validate_json(json_str)
        assert restored.smtp_host == info.smtp_host
        assert restored.smtp_port == info.smtp_port
        assert restored.from_email == info.from_email
        assert restored.to_emails == info.to_emails

    def test_model_dump_json_serializes_list(self) -> None:
        info = EmailSpecInfo(
            smtp_host="smtp.example.com",
            smtp_port=25,
            smtp_use_tls=False,
            smtp_timeout=30,
            from_email="from@example.com",
            to_emails=["a@example.com", "b@example.com"],
        )
        parsed = json.loads(info.model_dump_json())
        assert isinstance(parsed["to_emails"], list)
        assert len(parsed["to_emails"]) == 2
