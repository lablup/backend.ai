from __future__ import annotations

import smtplib
from unittest.mock import MagicMock

import pytest

from ai.backend.common.data.notification.types import (
    EmailMessage,
    EmailSpec,
    SMTPAuth,
    SMTPConnection,
)
from ai.backend.manager.errors.notification import (
    NotificationDeliveryFailure,
    NotificationProcessingFailure,
)
from ai.backend.manager.notification.channels.email.channel import EmailChannel
from ai.backend.manager.notification.types import NotificationMessage


@pytest.fixture
def channel() -> EmailChannel:
    return EmailChannel(
        email_spec=EmailSpec(
            smtp=SMTPConnection(host="smtp.example.com", port=587, use_tls=False),
            message=EmailMessage(from_email="noreply@example.com", to_emails=["ops@example.com"]),
            auth=SMTPAuth(username="mailer", password="secret"),
        )
    )


@pytest.fixture
def message() -> NotificationMessage:
    return NotificationMessage(message="Session ended")


def _smtp_raising(error: BaseException) -> MagicMock:
    """An ``smtplib.SMTP`` stand-in whose session raises ``error`` on login."""
    server = MagicMock()
    server.login.side_effect = error
    smtp = MagicMock()
    smtp.return_value.__enter__.return_value = server
    return smtp


class TestEmailChannelSend:
    @pytest.mark.parametrize(
        ("error", "reason"),
        [
            (
                smtplib.SMTPAuthenticationError(535, b"bad credentials"),
                "SMTP authentication failed",
            ),
            (smtplib.SMTPRecipientsRefused({}), "Email delivery failed"),
            (ConnectionRefusedError("refused"), "SMTP connection failed"),
            (TimeoutError("timed out"), "SMTP connection failed"),
        ],
        ids=["auth", "smtp-error", "connection-refused", "timeout"],
    )
    async def test_an_smtp_failure_is_a_client_visible_delivery_failure(
        self,
        channel: EmailChannel,
        message: NotificationMessage,
        monkeypatch: pytest.MonkeyPatch,
        error: BaseException,
        reason: str,
    ) -> None:
        monkeypatch.setattr(smtplib, "SMTP", _smtp_raising(error))

        with pytest.raises(NotificationDeliveryFailure, match=reason) as exc_info:
            await channel.send(message)

        assert exc_info.value.is_client_error()
        assert exc_info.value.__cause__ is error

    async def test_an_unexpected_error_stays_a_processing_failure(
        self,
        channel: EmailChannel,
        message: NotificationMessage,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setattr(smtplib, "SMTP", _smtp_raising(RuntimeError("bug")))

        with pytest.raises(NotificationProcessingFailure):
            await channel.send(message)
