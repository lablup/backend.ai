"""Email notification channel using SMTP."""

from __future__ import annotations

import asyncio
import errno
import logging
import smtplib
import socket
import ssl
from email.mime.text import MIMEText
from functools import partial

from ai.backend.common.data.notification.types import EmailSpec
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.errors.notification import (
    NotificationDeliveryFailure,
    NotificationProcessingFailure,
)
from ai.backend.manager.notification.channels.base import AbstractNotificationChannel
from ai.backend.manager.notification.types import NotificationMessage, SendResult

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

_DEFAULT_NOTIFICATION_SUBJECT = "Notification from Backend.AI"


_UNREACHABLE_ERRNOS = frozenset({
    errno.EHOSTUNREACH,
    errno.ENETUNREACH,
    errno.EHOSTDOWN,
    errno.ENETDOWN,
})


def _is_smtp_destination_failure(error: OSError) -> bool:
    """Whether the SMTP host could not be reached or presented a certificate that fails to verify."""
    if isinstance(
        error, (socket.gaierror, ConnectionError, TimeoutError, ssl.SSLCertVerificationError)
    ):
        return True
    return error.errno in _UNREACHABLE_ERRNOS


class EmailChannel(AbstractNotificationChannel):
    """Email notification channel using SMTP."""

    _spec: EmailSpec

    def __init__(self, email_spec: EmailSpec) -> None:
        """Initialize email channel with configuration."""
        self._spec = email_spec

    async def send(self, message: NotificationMessage) -> SendResult:
        """
        Send notification via email using SMTP.

        Args:
            message: Notification message to send

        Returns:
            SendResult indicating success

        Raises:
            NotificationDeliveryFailure: If the SMTP server cannot be reached or rejects the message
            NotificationProcessingFailure: If email delivery fails for any other reason
        """
        # Determine subject (priority: spec template > first line of message)
        if self._spec.message.subject_template:
            subject = self._spec.message.subject_template
        else:
            # Fallback: use first line of message as subject
            first_line = message.message.partition("\n")[0].strip()
            subject = first_line or _DEFAULT_NOTIFICATION_SUBJECT

        loop = asyncio.get_running_loop()
        await loop.run_in_executor(
            None,
            partial(self._send_email, subject, message.message),
        )

        log.info(
            "Email notification sent successfully to {} recipients",
            len(self._spec.message.to_emails),
        )

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
                rejected_recipients = server.send_message(
                    email_msg,
                    from_addr=msg.from_email,
                    to_addrs=msg.to_emails,
                )
                if rejected_recipients:
                    raise smtplib.SMTPRecipientsRefused(rejected_recipients)
        except smtplib.SMTPConnectError as e:
            log.exception(
                "Failed to connect to SMTP server {}:{}",
                smtp.host,
                smtp.port,
            )
            raise NotificationDeliveryFailure(f"SMTP connection failed: {e!s}") from e
        except smtplib.SMTPAuthenticationError as e:
            log.exception(
                "SMTP authentication failed for user {}",
                auth.username if auth else "unknown",
            )
            raise NotificationDeliveryFailure(f"SMTP authentication failed: {e!s}") from e
        except smtplib.SMTPException as e:
            log.exception("SMTP error while sending email")
            raise NotificationDeliveryFailure(f"Email delivery failed: {e!s}") from e
        except OSError as e:
            if not _is_smtp_destination_failure(e):
                log.exception("Unexpected error sending email")
                raise NotificationProcessingFailure(f"Email delivery failed: {e!s}") from e
            log.exception(
                "Failed to connect to SMTP server {}:{}",
                smtp.host,
                smtp.port,
            )
            raise NotificationDeliveryFailure(f"SMTP connection failed: {e!s}") from e
        except Exception as e:
            log.exception("Unexpected error sending email")
            raise NotificationProcessingFailure(f"Email delivery failed: {e!s}") from e
