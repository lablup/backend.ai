"""Stand-in for the side of a notification call that leaves the process.

A channel is validated by sending through it, and a rule by rendering its template and
sending the result. The rendering stays real; only the handler that would post to a
webhook or mail through SMTP is replaced with one that keeps the message and answers as
a delivered one would.
"""

from __future__ import annotations

from typing import override

import jinja2

from ai.backend.manager.data.notification import NotificationChannelData
from ai.backend.manager.notification.channels.base import AbstractNotificationChannel
from ai.backend.manager.notification.notification_center import NotificationCenter
from ai.backend.manager.notification.types import NotificationMessage, SendResult


class RecordingChannel(AbstractNotificationChannel):
    """보낸 메시지를 받아 적기만 한다."""

    _sent: list[str]

    def __init__(self, sent: list[str]) -> None:
        self._sent = sent

    @override
    async def send(self, message: NotificationMessage) -> SendResult:
        self._sent.append(message.message)
        return SendResult(message=message.message)


class FakeNotificationCenter(NotificationCenter):
    """실물과 같이 템플릿을 그리되, 보내는 자리만 받아 적는다.

    실물의 초기화는 HTTP 클라이언트 풀을 만들어 정리 작업을 띄우므로 부르지 않는다.
    """

    _sent: list[str]

    def __init__(self) -> None:
        self._template_env = jinja2.Environment(loader=jinja2.BaseLoader(), autoescape=False)
        self._sent = []

    @override
    def _create_handler(self, channel_data: NotificationChannelData) -> AbstractNotificationChannel:
        return RecordingChannel(self._sent)

    def sent(self) -> tuple[str, ...]:
        """무엇을 보냈는지, 부른 순서대로."""
        return tuple(self._sent)
