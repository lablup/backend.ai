"""Unit tests for EmailChannel."""

from __future__ import annotations

import smtplib
from collections.abc import Generator
from unittest.mock import MagicMock, patch

import pytest

from ai.backend.common.data.notification.types import (
    EmailMessage,
    EmailSpec,
    SMTPAuth,
    SMTPConnection,
)
from ai.backend.manager.errors.notification import NotificationProcessingFailure
from ai.backend.manager.notification.channels.email.channel import EmailChannel
from ai.backend.manager.notification.types import NotificationMessage, SendResult


class TestEmailChannel:
    """Test cases for EmailChannel."""

    @pytest.fixture
    def mock_smtp(self) -> Generator[MagicMock, None, None]:
        """
        Provide a mocked smtplib.SMTP context manager.

        The mock SMTP server has all methods (starttls, login, send_message)
        set up as successful MagicMocks by default.
        """
        with patch("ai.backend.manager.notification.channels.email.channel.smtplib") as mock_module:
            mock_server = MagicMock()
            mock_module.SMTP.return_value.__enter__ = MagicMock(return_value=mock_server)
            mock_module.SMTP.return_value.__exit__ = MagicMock(return_value=False)

            # Default success behavior
            mock_server.starttls = MagicMock()
            mock_server.login = MagicMock()
            mock_server.send_message = MagicMock()

            # Preserve real exception classes for error handling tests
            mock_module.SMTPConnectError = smtplib.SMTPConnectError
            mock_module.SMTPAuthenticationError = smtplib.SMTPAuthenticationError
            mock_module.SMTPException = smtplib.SMTPException

            yield mock_module

    @pytest.fixture
    def basic_spec(self) -> EmailSpec:
        """Basic email specification with authentication."""
        return EmailSpec(
            smtp=SMTPConnection(
                host="smtp.example.com",
                port=587,
            ),
            message=EmailMessage(
                from_email="noreply@example.com",
                to_emails=["admin@example.com"],
                subject_template="Test Notification",
            ),
            auth=SMTPAuth(
                username="user@example.com",
                password="password123",
            ),
        )

    @pytest.fixture
    def no_auth_spec(self) -> EmailSpec:
        """Specification without authentication (relay server)."""
        return EmailSpec(
            smtp=SMTPConnection(
                host="smtp.example.com",
                port=25,
                use_tls=False,
            ),
            message=EmailMessage(
                from_email="noreply@example.com",
                to_emails=["admin@example.com"],
            ),
        )

    @pytest.fixture
    def multi_recipient_spec(self) -> EmailSpec:
        """Specification with multiple recipients."""
        return EmailSpec(
            smtp=SMTPConnection(
                host="smtp.example.com",
                port=587,
            ),
            message=EmailMessage(
                from_email="noreply@example.com",
                to_emails=["admin1@example.com", "admin2@example.com", "admin3@example.com"],
            ),
            auth=SMTPAuth(
                username="user@example.com",
                password="password123",
            ),
        )

    @pytest.fixture
    def no_subject_spec(self) -> EmailSpec:
        """Specification without subject template (uses message first line)."""
        return EmailSpec(
            smtp=SMTPConnection(
                host="smtp.example.com",
                port=587,
            ),
            message=EmailMessage(
                from_email="noreply@example.com",
                to_emails=["admin@example.com"],
                subject_template=None,
            ),
            auth=SMTPAuth(
                username="user@example.com",
                password="password123",
            ),
        )

    # ============================================================
    # Tests: Success Cases
    # ============================================================

    @pytest.mark.asyncio
    async def test_send_success_with_auth(
        self,
        mock_smtp: MagicMock,
        basic_spec: EmailSpec,
    ) -> None:
        """Test successful email sending with authentication."""
        channel = EmailChannel(email_spec=basic_spec)
        message = NotificationMessage(message="Test notification message")

        result = await channel.send(message)

        assert isinstance(result, SendResult)
        # Verify SMTP was initialized with correct parameters
        mock_smtp.SMTP.assert_called_once_with(
            "smtp.example.com", 587, timeout=basic_spec.smtp.timeout
        )
        # Get the server instance from context manager
        mock_server = mock_smtp.SMTP.return_value.__enter__.return_value
        mock_server.starttls.assert_called_once()
        mock_server.login.assert_called_once_with("user@example.com", "password123")
        mock_server.send_message.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_success_without_auth(
        self,
        mock_smtp: MagicMock,
        no_auth_spec: EmailSpec,
    ) -> None:
        """Test successful email sending without authentication (relay server)."""
        channel = EmailChannel(email_spec=no_auth_spec)
        message = NotificationMessage(message="Test relay message")

        result = await channel.send(message)

        assert isinstance(result, SendResult)
        # Get the server instance from context manager
        mock_server = mock_smtp.SMTP.return_value.__enter__.return_value
        # No TLS and no login for relay server
        mock_server.starttls.assert_not_called()
        mock_server.login.assert_not_called()
        mock_server.send_message.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_to_multiple_recipients(
        self,
        mock_smtp: MagicMock,
        multi_recipient_spec: EmailSpec,
    ) -> None:
        """Test email is sent to all recipients."""
        channel = EmailChannel(email_spec=multi_recipient_spec)
        message = NotificationMessage(message="Test multi-recipient message")

        await channel.send(message)

        mock_server = mock_smtp.SMTP.return_value.__enter__.return_value
        sent_msg = mock_server.send_message.call_args[0][0]
        assert "admin1@example.com" in sent_msg["To"]
        assert "admin2@example.com" in sent_msg["To"]
        assert "admin3@example.com" in sent_msg["To"]

    @pytest.mark.asyncio
    async def test_subject_from_config_template(
        self,
        mock_smtp: MagicMock,
        basic_spec: EmailSpec,
    ) -> None:
        """Test email uses subject_template from spec."""
        channel = EmailChannel(email_spec=basic_spec)
        message = NotificationMessage(message="Test message body")

        await channel.send(message)

        mock_server = mock_smtp.SMTP.return_value.__enter__.return_value
        sent_msg = mock_server.send_message.call_args[0][0]
        # basic_config has subject_template="Test Notification"
        assert sent_msg["Subject"] == "Test Notification"

    @pytest.mark.asyncio
    async def test_subject_defaults_to_message_first_line(
        self,
        mock_smtp: MagicMock,
        no_subject_spec: EmailSpec,
    ) -> None:
        """Test subject defaults to first line of message when not provided."""
        channel = EmailChannel(email_spec=no_subject_spec)
        # No subject provided, should use first line of message
        message = NotificationMessage(message="First Line Subject\nRest of the message body")

        await channel.send(message)

        mock_server = mock_smtp.SMTP.return_value.__enter__.return_value
        sent_msg = mock_server.send_message.call_args[0][0]
        assert sent_msg["Subject"] == "First Line Subject"

    # ============================================================
    # Tests: Error Cases
    # ============================================================

    @pytest.mark.asyncio
    async def test_connection_error_raises_failure(
        self,
        mock_smtp: MagicMock,
        basic_spec: EmailSpec,
    ) -> None:
        """Test connection failure raises NotificationProcessingFailure."""
        mock_smtp.SMTP.return_value.__enter__.side_effect = smtplib.SMTPConnectError(
            421, "Connection refused"
        )
        channel = EmailChannel(email_spec=basic_spec)
        message = NotificationMessage(message="Test message")

        with pytest.raises(NotificationProcessingFailure):
            await channel.send(message)

    @pytest.mark.asyncio
    async def test_auth_error_raises_failure(
        self,
        mock_smtp: MagicMock,
        basic_spec: EmailSpec,
    ) -> None:
        """Test authentication failure raises NotificationProcessingFailure."""
        mock_server = mock_smtp.SMTP.return_value.__enter__.return_value
        mock_server.login.side_effect = smtplib.SMTPAuthenticationError(
            535, "Authentication failed"
        )
        channel = EmailChannel(email_spec=basic_spec)
        message = NotificationMessage(message="Test message")

        with pytest.raises(NotificationProcessingFailure):
            await channel.send(message)

    @pytest.mark.asyncio
    async def test_smtp_error_raises_failure(
        self,
        mock_smtp: MagicMock,
        basic_spec: EmailSpec,
    ) -> None:
        """Test SMTP error raises NotificationProcessingFailure."""
        mock_server = mock_smtp.SMTP.return_value.__enter__.return_value
        mock_server.send_message.side_effect = smtplib.SMTPException("SMTP error")
        channel = EmailChannel(email_spec=basic_spec)
        message = NotificationMessage(message="Test message")

        with pytest.raises(NotificationProcessingFailure):
            await channel.send(message)

    @pytest.mark.asyncio
    async def test_use_tls_option(
        self,
        mock_smtp: MagicMock,
        basic_spec: EmailSpec,
    ) -> None:
        """Test use_tls option controls STARTTLS."""
        # Test with TLS enabled (default)
        channel = EmailChannel(email_spec=basic_spec)
        message = NotificationMessage(message="Test message")

        await channel.send(message)

        mock_server = mock_smtp.SMTP.return_value.__enter__.return_value
        mock_server.starttls.assert_called_once()

    @pytest.mark.asyncio
    async def test_timeout_passed_to_smtp(
        self,
        mock_smtp: MagicMock,
    ) -> None:
        """Test timeout is passed to SMTP constructor."""
        spec = EmailSpec(
            smtp=SMTPConnection(
                host="smtp.example.com",
                port=587,
                timeout=120,
            ),
            message=EmailMessage(
                from_email="noreply@example.com",
                to_emails=["admin@example.com"],
            ),
        )
        channel = EmailChannel(email_spec=spec)
        message = NotificationMessage(message="Test message")

        await channel.send(message)

        mock_smtp.SMTP.assert_called_once_with("smtp.example.com", 587, timeout=120)
