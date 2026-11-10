"""Email notification channel using SMTP."""

from __future__ import annotations

import logging
import smtplib
from email.mime.text import MIMEText
from functools import partial
from typing import override

from ai.backend.common.asyncio import run_in_executor_with_context
from ai.backend.common.data.notification.types import EmailSpec
from ai.backend.logging.structured import StructuredLogger
from ai.backend.manager.errors.notification import NotificationProcessingFailure
from ai.backend.manager.notification.channels.base import AbstractNotificationChannel
from ai.backend.manager.notification.types import NotificationMessage, SendResult

log = StructuredLogger(logging.getLogger(__spec__.name))

_DEFAULT_NOTIFICATION_SUBJECT = "Notification from Backend.AI"


class EmailChannel(AbstractNotificationChannel):
    """Email notification channel using SMTP."""

    _spec: EmailSpec

    def __init__(self, email_spec: EmailSpec) -> None:
        """Initialize email channel with configuration."""
        self._spec = email_spec

    @override
    async def send(self, message: NotificationMessage) -> SendResult:
        """
        Send notification via email using SMTP.

        Args:
            message: Notification message to send

        Returns:
            SendResult indicating success

        Raises:
            NotificationProcessingFailure: If email delivery fails
        """
        # Determine subject (priority: spec template > first line of message)
        if self._spec.message.subject_template:
            subject = self._spec.message.subject_template
        else:
            # Fallback: use first line of message as subject
            lines = message.message.split("\n", 1)
            subject = lines[0] if lines else _DEFAULT_NOTIFICATION_SUBJECT

        await run_in_executor_with_context(
            None,
            partial(self._send_email, subject, message.message),
        )

        log.trace("email notification sent", recipient_count=len(self._spec.message.to_emails))

        return SendResult(
            message=f"Email sent successfully to {len(self._spec.message.to_emails)} recipients"
        )

    def _send_email(self, subject: str, body: str) -> None:
        """
        Send email synchronously via SMTP.

        This method runs in a thread pool executor.
        """
        smtp = self._spec.smtp
        msg = self._spec.message

        email_msg = MIMEText(body, "plain", "utf-8")
        email_msg["Subject"] = subject
        email_msg["From"] = msg.from_email
        email_msg["To"] = ",".join(msg.to_emails)

        auth = self._spec.auth
        try:
            with smtplib.SMTP(smtp.host, smtp.port, timeout=smtp.timeout) as server:
                if smtp.use_tls:
                    server.starttls()
                if auth and auth.username and auth.password:
                    server.login(auth.username, auth.password)
                server.send_message(
                    email_msg,
                    from_addr=msg.from_email,
                    to_addrs=msg.to_emails,
                )
        except smtplib.SMTPConnectError as e:
            raise NotificationProcessingFailure(f"SMTP connection failed: {e!s}") from e
        except smtplib.SMTPAuthenticationError as e:
            raise NotificationProcessingFailure(f"SMTP authentication failed: {e!s}") from e
        except smtplib.SMTPException as e:
            raise NotificationProcessingFailure(f"Email delivery failed: {e!s}") from e
        except Exception as e:
            raise NotificationProcessingFailure(f"Email delivery failed: {e!s}") from e
