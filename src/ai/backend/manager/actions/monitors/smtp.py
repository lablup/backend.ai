import asyncio
import enum
from dataclasses import dataclass
from datetime import datetime
from email.mime.text import MIMEText
from typing import Final, override

import aiosmtplib

from ai.backend.manager.models.audit_log import OperationStatus

from ...actions.action import BaseAction, ProcessResult
from .monitor import ActionMonitor

UNKNOWN_ENTITY_ID: Final[str] = "(unknown)"


class SMTPTriggerPolicy(enum.Flag):
    PRE_ACTION = enum.auto()
    POST_ACTION = enum.auto()
    ON_ERROR = enum.auto()


@dataclass
class SMTPReporterConfig:
    host: str
    port: int
    username: str
    password: str
    sender: str
    recipients: list[str]
    use_tls: bool
    trigger_policy: SMTPTriggerPolicy


class SMTPReporter(ActionMonitor):
    def __init__(self, config: SMTPReporterConfig, concurrency_limit: int = 5) -> None:
        self._config = config
        self._semaphore = asyncio.Semaphore(concurrency_limit)

    def _make_subject(self, action: BaseAction) -> str:
        return f"Backend.AI SMTP Log Alert ({action.entity_type()}:{action.operation_type()})"

    async def _send_email(self, subject: str, email_body: str) -> None:
        async with self._semaphore:
            email_body += "\nThis email is sent from Backend.AI SMTP Reporter"

            message = MIMEText(email_body, "plain", "utf-8")
            message["Subject"] = subject
            message["From"] = self._config.sender
            message["To"] = ",".join(self._config.recipients)

            smtp = aiosmtplib.SMTP(
                hostname=self._config.host,
                port=self._config.port,
                use_tls=self._config.use_tls,
            )

            try:
                await smtp.connect()
                await smtp.login(self._config.username, self._config.password)
                await smtp.send_message(
                    message, sender=self._config.sender, recipients=self._config.recipients
                )
            except Exception as e:
                print(f"Failed to send email: {e}")
            finally:
                await smtp.quit()

    @override
    async def prepare(self, action: BaseAction) -> None:
        if SMTPTriggerPolicy.PRE_ACTION in self._config.trigger_policy:
            subject = self._make_subject(action)
            body = (
                f"Status: {OperationStatus.RUNNING}\n"
                f"Description: Task is running...\n"
                f"Started at: {datetime.now()}\n"
            )
            asyncio.create_task(self._send_email(subject, body))

    @override
    async def done(self, action: BaseAction, result: ProcessResult) -> None:
        if SMTPTriggerPolicy.ON_ERROR in self._config.trigger_policy:
            if result.meta.status == OperationStatus.ERROR:
                subject = self._make_subject(action)
                body = (
                    f"Entity ID: {result.result.entity_id() if result.result else UNKNOWN_ENTITY_ID}\n"
                    f"Status: {result.meta.status}\n"
                    f"Description: {result.meta.description}\n"
                    f"Started at: {result.meta.started_at}\n"
                    f"Ended at: {result.meta.end_at}\n"
                    f"Duration: {result.meta.duration} seconds\n"
                )
                asyncio.create_task(self._send_email(subject, body))

        if SMTPTriggerPolicy.POST_ACTION in self._config.trigger_policy:
            subject = self._make_subject(action)
            body = (
                f"Entity ID: {result.result.entity_id() if result.result else UNKNOWN_ENTITY_ID}\n"
                f"Status: {result.meta.status}\n"
                f"Description: {result.meta.description}\n"
                f"Started at: {result.meta.started_at}\n"
                f"Ended at: {result.meta.end_at}\n"
                f"Duration: {result.meta.duration} seconds\n"
            )
            asyncio.create_task(self._send_email(subject, body))
