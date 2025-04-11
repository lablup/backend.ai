import asyncio
import logging
from abc import abstractmethod
from dataclasses import dataclass
from datetime import datetime
from email.mime.text import MIMEText
from typing import Final

import aiosmtplib

from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.models.audit_log import OperationStatus
from ai.backend.manager.reporters.types import (
    AbstractReporter,
    FinishedActionMessage,
    StartedActionMessage,
)
from ai.backend.manager.types import SMTPTriggerPolicy

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


UNKNOWN_ENTITY_ID: Final[str] = "(unknown)"


@dataclass
class SMTPSenderArgs:
    host: str
    port: int
    username: str
    password: str
    sender: str
    recipients: list[str]
    use_tls: bool
    concurrency_limit: int = 5


class SMTPSender:
    _smtp: aiosmtplib.SMTP
    _smtp_lock: asyncio.Lock
    _config: SMTPSenderArgs

    def __init__(self, args: SMTPSenderArgs) -> None:
        self._config = args
        self._smtp = aiosmtplib.SMTP(hostname=args.host, port=args.port, use_tls=args.use_tls)
        self._smtp_lock = asyncio.Lock()

    async def _connect_smtp(self) -> None:
        async with self._smtp_lock:
            try:
                if not self._smtp.is_connected:
                    await self._smtp.connect()
                    await self._smtp.login(self._config.username, self._config.password)
            except Exception as e:
                log.warning(f"Failed to connect to SMTP server: {e}. Retrying...")
                self._smtp = aiosmtplib.SMTP(
                    hostname=self._config.host, port=self._config.port, use_tls=self._config.use_tls
                )
                await self._smtp.connect()
                await self._smtp.login(self._config.username, self._config.password)

    async def send_email(self, subject: str, email_body: str) -> None:
        email_body += "\nThis email is sent from Backend.AI SMTP Reporter"

        message = MIMEText(email_body, "plain", "utf-8")
        message["Subject"] = subject
        message["From"] = self._config.sender
        message["To"] = ",".join(self._config.recipients)

        try:
            await self._connect_smtp()
            await self._smtp.send_message(
                message, sender=self._config.sender, recipients=self._config.recipients
            )
        except Exception as e:
            print(f"Failed to send email: {e}")


class SMTPReporter(AbstractReporter):
    _smtp_sender: SMTPSender

    def __init__(self, args: SMTPSenderArgs, trigger_policy: SMTPTriggerPolicy) -> None:
        self._smtp_sender = SMTPSender(args)
        self._trigger_policy = trigger_policy

    def _make_subject(self, action_type: str) -> str:
        return f"Backend.AI SMTP Log Alert ({action_type})"

    @abstractmethod
    async def report_started(self, message: StartedActionMessage) -> None:
        if self._trigger_policy == SMTPTriggerPolicy.ON_ERROR:
            return

        subject = self._make_subject(message.action_type)
        body = (
            "Action has been triggered.\n\n"
            f"Action type: ({message.action_type})\n"
            f"Status: {OperationStatus.RUNNING}\n"
            f"Description: Task is running...\n"
            f"Started at: {datetime.now()}\n"
        )
        asyncio.create_task(self._smtp_sender.send_email(subject, body))

    @abstractmethod
    async def report_finished(self, message: FinishedActionMessage) -> None:
        if self._trigger_policy == SMTPTriggerPolicy.ON_ERROR:
            if message.status == OperationStatus.ERROR:
                subject = self._make_subject(message.action_type)
                body = (
                    "Action has resulted in an error.\n\n"
                    f"Action type: ({message.action_type})\n"
                    f"Entity ID: {message.entity_id or UNKNOWN_ENTITY_ID}\n"
                    f"Status: {message.status}\n"
                    f"Description: {message.description}\n"
                    f"Started at: {message.created_at}\n"
                    f"Ended at: {message.ended_at}\n"
                    f"Duration: {message.duration} seconds\n"
                )
                asyncio.create_task(self._smtp_sender.send_email(subject, body))

        subject = self._make_subject(message.action_type)
        body = (
            "Action has been completed.\n\n"
            f"Action type: ({message.action_type})\n"
            f"Entity ID: {message.entity_id or UNKNOWN_ENTITY_ID}\n"
            f"Status: {message.status}\n"
            f"Description: {message.description}\n"
            f"Started at: {message.created_at}\n"
            f"Ended at: {message.ended_at}\n"
            f"Duration: {message.duration} seconds\n"
        )
        asyncio.create_task(self._smtp_sender.send_email(subject, body))
