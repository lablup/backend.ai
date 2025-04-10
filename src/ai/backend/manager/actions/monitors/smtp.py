import asyncio
import enum
import logging
from dataclasses import dataclass
from datetime import datetime
from email.mime.text import MIMEText
from typing import Final, override

import aiosmtplib

from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.models.audit_log import OperationStatus

from ...actions.action import BaseAction, ProcessResult
from .monitor import ActionMonitor

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


UNKNOWN_ENTITY_ID: Final[str] = "(unknown)"


class SMTPTriggerPolicy(enum.Flag):
    PRE_ACTION = enum.auto()
    POST_ACTION = enum.auto()
    ON_ERROR = enum.auto()


@dataclass
class SMTPReporterArgs:
    host: str
    port: int
    username: str
    password: str
    sender: str
    recipients: list[str]
    use_tls: bool
    trigger_policy: SMTPTriggerPolicy
    concurrency_limit: int = 5


class SMTPReporter(ActionMonitor):
    _closed: bool
    _config: SMTPReporterArgs
    _task_queue: asyncio.Queue[tuple[str, str]]
    _send_email_workers: list[asyncio.Task]
    _smtp: aiosmtplib.SMTP
    _smtp_lock: asyncio.Lock

    def __init__(self, args: SMTPReporterArgs) -> None:
        self._closed = True
        self._config = args
        self._task_queue = asyncio.Queue()
        self._smtp = aiosmtplib.SMTP(
            hostname=self._config.host, port=self._config.port, use_tls=self._config.use_tls
        )
        self._smtp_lock = asyncio.Lock()

    def _make_subject(self, action: BaseAction) -> str:
        return f"Backend.AI SMTP Log Alert ({action.get_type()})"

    async def _send_email_worker(self) -> None:
        while not self._closed:
            subject, email_body = await self._task_queue.get()
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
            finally:
                self._task_queue.task_done()

    async def _send_email(self, subject: str, email_body: str) -> None:
        await self._task_queue.put((subject, email_body))

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

    async def start(self) -> None:
        self._closed = False
        await self._connect_smtp()
        self._send_email_workers = []
        for _ in range(self._config.concurrency_limit):
            worker = asyncio.create_task(self._send_email_worker())
            self._send_email_workers.append(worker)

    async def stop(self) -> None:
        self._closed = True
        await self._task_queue.join()
        for worker in self._send_email_workers:
            worker.cancel()
        self._send_email_workers = []

        async with self._smtp_lock:
            if self._smtp.is_connected:
                await self._smtp.quit()

    @override
    async def prepare(self, action: BaseAction) -> None:
        if SMTPTriggerPolicy.PRE_ACTION in self._config.trigger_policy:
            subject = self._make_subject(action)
            body = (
                "Action has been triggered.\n\n"
                f"Action type: ({action.get_type()})\n"
                f"Status: {OperationStatus.RUNNING}\n"
                f"Description: Task is running...\n"
                f"Started at: {datetime.now()}\n"
            )
            await self._send_email(subject, body)

    @override
    async def done(self, action: BaseAction, result: ProcessResult) -> None:
        if SMTPTriggerPolicy.ON_ERROR in self._config.trigger_policy:
            if result.meta.status == OperationStatus.ERROR:
                subject = self._make_subject(action)
                body = (
                    "Action has resulted in an error.\n\n"
                    f"Action type: ({action.get_type()})\n"
                    f"Entity ID: {result.result.entity_id() if result.result else UNKNOWN_ENTITY_ID}\n"
                    f"Status: {result.meta.status}\n"
                    f"Description: {result.meta.description}\n"
                    f"Started at: {result.meta.started_at}\n"
                    f"Ended at: {result.meta.end_at}\n"
                    f"Duration: {result.meta.duration} seconds\n"
                )
                await self._send_email(subject, body)

        if SMTPTriggerPolicy.POST_ACTION in self._config.trigger_policy:
            subject = self._make_subject(action)
            body = (
                "Action has been completed.\n\n"
                f"Action type: ({action.get_type()})\n"
                f"Entity ID: {result.result.entity_id() if result.result else UNKNOWN_ENTITY_ID}\n"
                f"Status: {result.meta.status}\n"
                f"Description: {result.meta.description}\n"
                f"Started at: {result.meta.started_at}\n"
                f"Ended at: {result.meta.end_at}\n"
                f"Duration: {result.meta.duration} seconds\n"
            )
            await self._send_email(subject, body)
