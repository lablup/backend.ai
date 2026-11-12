from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch

import pytest

from ai.backend.common.data.entity.notification import NotificationChannelID
from ai.backend.common.data.notification import SessionStartedMessage
from ai.backend.common.data.notification.types import (
    NotificationChannelType,
    NotificationRuleType,
    WebhookSpec,
)
from ai.backend.manager.data.notification.types import NotificationChannelData
from ai.backend.manager.errors.notification import NotificationTemplateRenderingFailure
from ai.backend.manager.notification.notification_center import NotificationCenter
from ai.backend.manager.notification.types import ProcessRuleParams


@pytest.fixture()
async def notification_center() -> AsyncGenerator[NotificationCenter, None]:
    nc = NotificationCenter()
    yield nc
    await nc.close()


def _params(message_template: str) -> ProcessRuleParams:
    now = datetime.now(tz=UTC)
    return ProcessRuleParams(
        message_template=message_template,
        rule_type=NotificationRuleType.SESSION_STARTED,
        channel=NotificationChannelData(
            id=NotificationChannelID(uuid.uuid4()),
            name="test-webhook",
            description=None,
            channel_type=NotificationChannelType.WEBHOOK,
            spec=WebhookSpec(url="https://example.com/webhook"),
            enabled=True,
            created_by=uuid.uuid4(),
            created_at=now,
            updated_at=now,
        ),
        timestamp=now,
        notification_data=SessionStartedMessage(
            session_id=str(uuid.uuid4()),
            session_name="test-session",
            session_type="interactive",
            cluster_mode="single-node",
            status="RUNNING",
        ),
    )


class TestProcessRuleTemplateSandbox:
    @pytest.mark.parametrize(
        "message_template",
        [
            "{{ data.__class__.__mro__ }}",
            "{{ data.update(session_name='x') }}",
        ],
        ids=["dunder-attribute", "mutating-call"],
    )
    async def test_an_unsafe_template_fails_to_render(
        self,
        notification_center: NotificationCenter,
        message_template: str,
    ) -> None:
        with pytest.raises(NotificationTemplateRenderingFailure):
            await notification_center.process_rule(_params(message_template))

    async def test_a_plain_template_renders_the_message_fields(
        self,
        notification_center: NotificationCenter,
    ) -> None:
        handler = AsyncMock()
        with patch.object(notification_center, "_create_handler", return_value=handler):
            await notification_center.process_rule(
                _params("Session {{ session_name }} started ({{ data.session_type }})")
            )

        sent = handler.send.await_args.args[0]
        assert sent.message == "Session test-session started (interactive)"
