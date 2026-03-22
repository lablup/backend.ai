"""Tests for ai.backend.common.dto.manager.v2.notification.types module."""

from __future__ import annotations

import json

from ai.backend.common.data.notification.types import (
    NotificationChannelType,
    NotificationRuleType,
)
from ai.backend.common.dto.manager.v2.notification.types import (
    EmailMessageInfo,
    EmailSpecInfo,
    NotificationChannelOrderField,
    NotificationChannelTypeDTO,
    NotificationRuleOrderField,
    NotificationRuleTypeDTO,
    OrderDirection,
    SMTPAuthInfo,
    SMTPConnectionInfo,
    WebhookSpecInfo,
)


class TestOrderDirection:
    """Tests for OrderDirection enum."""

    def test_asc_value(self) -> None:
        assert OrderDirection.ASC.value == "ASC"

    def test_desc_value(self) -> None:
        assert OrderDirection.DESC.value == "DESC"

    def test_all_values_are_strings(self) -> None:
        for member in OrderDirection:
            assert isinstance(member.value, str)

    def test_enum_members_count(self) -> None:
        members = list(OrderDirection)
        assert len(members) == 2

    def test_from_string_asc(self) -> None:
        assert OrderDirection("ASC") is OrderDirection.ASC

    def test_from_string_desc(self) -> None:
        assert OrderDirection("DESC") is OrderDirection.DESC


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


class TestNotificationChannelTypeDTO:
    """Tests for NotificationChannelTypeDTO enum (DTO layer, distinct from data layer)."""

    def test_webhook_value(self) -> None:
        assert NotificationChannelTypeDTO.WEBHOOK.value == "webhook"

    def test_email_value(self) -> None:
        assert NotificationChannelTypeDTO.EMAIL.value == "email"

    def test_enum_members_count(self) -> None:
        assert len(list(NotificationChannelTypeDTO)) == 2

    def test_matches_data_layer_values(self) -> None:
        # Verifies adapter can convert DTO values to data layer values directly.
        for dto_member in NotificationChannelTypeDTO:
            data_member = NotificationChannelType(dto_member.value)
            assert data_member.value == dto_member.value


class TestNotificationRuleTypeDTO:
    """Tests for NotificationRuleTypeDTO enum (DTO layer, distinct from data layer)."""

    def test_session_started_value(self) -> None:
        assert NotificationRuleTypeDTO.SESSION_STARTED.value == "session.started"

    def test_session_terminated_value(self) -> None:
        assert NotificationRuleTypeDTO.SESSION_TERMINATED.value == "session.terminated"

    def test_artifact_download_completed_value(self) -> None:
        assert (
            NotificationRuleTypeDTO.ARTIFACT_DOWNLOAD_COMPLETED.value
            == "artifact.download.completed"
        )

    def test_endpoint_lifecycle_changed_value(self) -> None:
        assert (
            NotificationRuleTypeDTO.ENDPOINT_LIFECYCLE_CHANGED.value == "endpoint.lifecycle.changed"
        )

    def test_enum_members_count(self) -> None:
        assert len(list(NotificationRuleTypeDTO)) == 4

    def test_matches_data_layer_values(self) -> None:
        # Verifies adapter can convert DTO values to data layer values directly.
        for dto_member in NotificationRuleTypeDTO:
            data_member = NotificationRuleType(dto_member.value)
            assert data_member.value == dto_member.value


class TestWebhookSpecInfo:
    """Tests for WebhookSpecInfo response sub-model."""

    def test_creation_with_url(self) -> None:
        info = WebhookSpecInfo(
            channel_type=NotificationChannelTypeDTO.WEBHOOK,
            url="https://example.com/webhook",
        )
        assert info.url == "https://example.com/webhook"

    def test_creation_from_dict(self) -> None:
        info = WebhookSpecInfo.model_validate({
            "channel_type": "webhook",
            "url": "https://hooks.example.com",
        })
        assert info.url == "https://hooks.example.com"

    def test_model_dump_json(self) -> None:
        info = WebhookSpecInfo(
            channel_type=NotificationChannelTypeDTO.WEBHOOK,
            url="https://example.com/hook",
        )
        parsed = json.loads(info.model_dump_json())
        assert parsed["url"] == "https://example.com/hook"

    def test_round_trip_serialization(self) -> None:
        info = WebhookSpecInfo(
            channel_type=NotificationChannelTypeDTO.WEBHOOK,
            url="https://example.com/hook",
        )
        json_str = info.model_dump_json()
        restored = WebhookSpecInfo.model_validate_json(json_str)
        assert restored.url == info.url


class TestEmailSpecInfo:
    """Tests for EmailSpecInfo response sub-model."""

    def test_creation_with_all_fields(self) -> None:
        smtp = SMTPConnectionInfo(
            host="smtp.example.com",
            port=587,
            use_tls=True,
            timeout=30,
        )
        message = EmailMessageInfo(
            from_email="noreply@example.com",
            to_emails=["admin@example.com", "ops@example.com"],
        )
        info = EmailSpecInfo(
            channel_type=NotificationChannelTypeDTO.EMAIL,
            smtp=smtp,
            message=message,
        )
        assert info.smtp.host == "smtp.example.com"
        assert info.smtp.port == 587
        assert info.smtp.use_tls is True
        assert info.smtp.timeout == 30
        assert info.message.from_email == "noreply@example.com"
        assert info.message.to_emails == ["admin@example.com", "ops@example.com"]

    def test_creation_from_dict(self) -> None:
        info = EmailSpecInfo.model_validate({
            "channel_type": "email",
            "smtp": {
                "host": "mail.example.com",
                "port": 465,
                "use_tls": False,
                "timeout": 60,
            },
            "message": {
                "from_email": "sender@example.com",
                "to_emails": ["recipient@example.com"],
            },
        })
        assert info.smtp.host == "mail.example.com"
        assert info.smtp.port == 465

    def test_round_trip_serialization(self) -> None:
        smtp = SMTPConnectionInfo(host="smtp.example.com", port=587, use_tls=True, timeout=30)
        message = EmailMessageInfo(
            from_email="noreply@example.com",
            to_emails=["admin@example.com"],
        )
        info = EmailSpecInfo(
            channel_type=NotificationChannelTypeDTO.EMAIL,
            smtp=smtp,
            message=message,
        )
        json_str = info.model_dump_json()
        restored = EmailSpecInfo.model_validate_json(json_str)
        assert restored.smtp.host == info.smtp.host
        assert restored.smtp.port == info.smtp.port
        assert restored.message.from_email == info.message.from_email
        assert restored.message.to_emails == info.message.to_emails

    def test_model_dump_json_serializes_list(self) -> None:
        smtp = SMTPConnectionInfo(host="smtp.example.com", port=25, use_tls=False, timeout=30)
        message = EmailMessageInfo(
            from_email="from@example.com",
            to_emails=["a@example.com", "b@example.com"],
        )
        info = EmailSpecInfo(
            channel_type=NotificationChannelTypeDTO.EMAIL,
            smtp=smtp,
            message=message,
        )
        parsed = json.loads(info.model_dump_json())
        assert isinstance(parsed["message"]["to_emails"], list)
        assert len(parsed["message"]["to_emails"]) == 2

    def test_auth_defaults_to_none(self) -> None:
        smtp = SMTPConnectionInfo(host="smtp.example.com", port=587, use_tls=True, timeout=30)
        message = EmailMessageInfo(from_email="from@example.com", to_emails=["to@example.com"])
        info = EmailSpecInfo(
            channel_type=NotificationChannelTypeDTO.EMAIL,
            smtp=smtp,
            message=message,
        )
        assert info.auth is None

    def test_with_auth(self) -> None:
        smtp = SMTPConnectionInfo(host="smtp.example.com", port=587, use_tls=True, timeout=30)
        message = EmailMessageInfo(from_email="from@example.com", to_emails=["to@example.com"])
        auth = SMTPAuthInfo(username="user@example.com")
        info = EmailSpecInfo(
            channel_type=NotificationChannelTypeDTO.EMAIL,
            smtp=smtp,
            message=message,
            auth=auth,
        )
        assert info.auth is not None
        assert info.auth.username == "user@example.com"
