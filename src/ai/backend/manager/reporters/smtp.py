import logging
import smtplib
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from email.mime.text import MIMEText
from typing import Final, override

from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.actions.types import OperationStatus
from ai.backend.manager.reporters.base import (
    AbstractReporter,
    FinishedActionMessage,
    StartedActionMessage,
)
from ai.backend.manager.types import SMTPTriggerPolicy

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


_UNDEFINED_VALUE: Final[str] = "(undefined)"


@dataclass
class SMTPSenderArgs:
    host: str
    port: int
    username: str
    password: str
    sender: str
    recipients: list[str]
    use_tls: bool
    template: str
    max_workers: int


class SMTPSender:
    def __init__(self, args: SMTPSenderArgs) -> None:
        self._config = args
        self._executor = ThreadPoolExecutor(max_workers=self._config.max_workers)

    def send_email(self, subject: str, email_body: str) -> None:
        self._executor.submit(self._send_email, subject, email_body)

    def _send_email(self, subject: str, email_body: str) -> None:
        message = MIMEText(email_body, "plain", "utf-8")
        message["Subject"] = subject
        message["From"] = self._config.sender
        message["To"] = ",".join(self._config.recipients)

        try:
            with smtplib.SMTP(self._config.host, self._config.port) as server:
                if self._config.use_tls:
                    server.starttls()
                server.login(self._config.username, self._config.password)
                server.send_message(
                    message,
                    from_addr=self._config.sender,
                    to_addrs=self._config.recipients,
                )
        except Exception as e:
            log.error(f"Failed to send email: {e}")


class SMTPReporter(AbstractReporter):
    _mail_template: str
    _smtp_sender: SMTPSender

    def __init__(self, args: SMTPSenderArgs, trigger_policy: SMTPTriggerPolicy) -> None:
        self._smtp_sender = SMTPSender(args)
        self._trigger_policy = trigger_policy
        self._mail_template = args.template

    def _create_body_from_template(self, message: FinishedActionMessage) -> str:
        template = self._mail_template

        template = template.replace("{{ action_id }}", str(message.action_id))
        template = template.replace("{{ action_type }}", message.action_type)
        template = template.replace(
            "{{ entity_id }}", str(message.entity_id) if message.entity_id else _UNDEFINED_VALUE
        )
        template = template.replace("{{ request_id }}", message.request_id or _UNDEFINED_VALUE)
        template = template.replace("{{ entity_type }}", message.entity_type)
        template = template.replace("{{ operation_type }}", message.operation_type)
        template = template.replace("{{ created_at }}", str(message.created_at))
        template = template.replace("{{ ended_at }}", str(message.ended_at))
        template = template.replace("{{ duration }}", str(message.duration))
        template = template.replace("{{ status }}", message.status.value)
        template = template.replace("{{ description }}", message.description)

        return template

    def _make_subject(self, action_type: str) -> str:
        return f"Backend.AI SMTP Log Alert ({action_type})"

    @override
    async def report_started(self, message: StartedActionMessage) -> None:
        pass

    @override
    async def report_finished(self, message: FinishedActionMessage) -> None:
        if self._trigger_policy == SMTPTriggerPolicy.ON_ERROR:
            if message.status == OperationStatus.ERROR:
                subject = self._make_subject(message.action_type)
                body = (
                    "Action has resulted in an error.\n\n"
                    f"{self._create_body_from_template(message)}"
                )
                self._smtp_sender.send_email(subject, body)
                return

        subject = self._make_subject(message.action_type)
        body = f"Action has finished.\n\n{self._create_body_from_template(message)}"
        self._smtp_sender.send_email(subject, body)
