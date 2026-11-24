from __future__ import annotations

import errno
import smtplib
import ssl
from dataclasses import dataclass
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


@dataclass(frozen=True)
class _SubjectCase:
    name: str
    message: str
    expected_subject: str


@pytest.fixture
def smtp_session_accepting_every_recipient(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    smtp_session = MagicMock()
    smtp_session.send_message.return_value = {}
    smtp = MagicMock()
    smtp.return_value.__enter__.return_value = smtp_session
    monkeypatch.setattr(smtplib, "SMTP", smtp)
    return smtp_session


@pytest.fixture
def channel_with_one_of_two_recipients_rejected(monkeypatch: pytest.MonkeyPatch) -> EmailChannel:
    smtp = MagicMock()
    smtp.return_value.__enter__.return_value.send_message.return_value = {
        "left-the-company@example.com": (550, b"5.1.1 User unknown")
    }
    monkeypatch.setattr(smtplib, "SMTP", smtp)
    return EmailChannel(
        email_spec=EmailSpec(
            smtp=SMTPConnection(host="smtp.example.com", port=587, use_tls=False),
            message=EmailMessage(
                from_email="noreply@example.com",
                to_emails=["ops@example.com", "left-the-company@example.com"],
            ),
        )
    )


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
            (OSError(errno.EHOSTUNREACH, "No route to host"), "SMTP connection failed"),
            (ssl.SSLCertVerificationError("certificate has expired"), "SMTP connection failed"),
        ],
        ids=["auth", "smtp-error", "connection-refused", "timeout", "no-route", "bad-certificate"],
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

        assert exc_info.value.status_code == 400
        assert exc_info.value.__cause__ is error

    @pytest.mark.parametrize(
        "error",
        [RuntimeError("bug"), OSError(24, "Too many open files")],
        ids=["bug", "local-os-error"],
    )
    async def test_an_unexpected_error_stays_a_processing_failure(
        self,
        channel: EmailChannel,
        message: NotificationMessage,
        monkeypatch: pytest.MonkeyPatch,
        error: BaseException,
    ) -> None:
        monkeypatch.setattr(smtplib, "SMTP", _smtp_raising(error))

        with pytest.raises(NotificationProcessingFailure):
            await channel.send(message)

    async def test_a_rejection_of_some_recipients_is_a_delivery_failure_naming_them(
        self,
        channel_with_one_of_two_recipients_rejected: EmailChannel,
        message: NotificationMessage,
    ) -> None:
        with pytest.raises(
            NotificationDeliveryFailure, match=r"left-the-company@example\.com.*550"
        ):
            await channel_with_one_of_two_recipients_rejected.send(message)

    @pytest.mark.parametrize(
        "case",
        [
            _SubjectCase(
                name="first-line",
                message="Session ended\nSession id: 1",
                expected_subject="Session ended",
            ),
            _SubjectCase(
                name="empty-message",
                message="",
                expected_subject="Notification from Backend.AI",
            ),
            _SubjectCase(
                name="empty-first-line",
                message="\nSession ended",
                expected_subject="Notification from Backend.AI",
            ),
            _SubjectCase(
                name="blank-first-line",
                message=" \r\nSession ended",
                expected_subject="Notification from Backend.AI",
            ),
        ],
        ids=lambda case: case.name,
    )
    async def test_the_subject_is_the_first_line_unless_it_is_blank(
        self,
        channel: EmailChannel,
        smtp_session_accepting_every_recipient: MagicMock,
        case: _SubjectCase,
    ) -> None:
        await channel.send(NotificationMessage(message=case.message))

        sent_email = smtp_session_accepting_every_recipient.send_message.call_args.args[0]
        assert sent_email["Subject"] == case.expected_subject
