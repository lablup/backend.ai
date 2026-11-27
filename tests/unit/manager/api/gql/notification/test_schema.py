"""The channel and strategy specs expose their concrete settings as oneOf-shaped objects."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from graphql import GraphQLObjectType

from ai.backend.common.data.model_deployment.types import DeploymentStrategy
from ai.backend.common.dto.manager.v2.deployment.response import DeploymentPolicyNode
from ai.backend.common.dto.manager.v2.deployment.types import (
    BlueGreenStrategySpecInfo,
    DeploymentStrategySpecInfo,
    RollingUpdateStrategySpecInfo,
)
from ai.backend.common.dto.manager.v2.notification.response import NotificationChannelNode
from ai.backend.common.dto.manager.v2.notification.types import (
    EmailMessageInfo,
    EmailSpecInfo,
    NotificationChannelSpecInfo,
    NotificationChannelTypeDTO,
    SMTPAuthInfo,
    SMTPConnectionInfo,
    WebhookSpecInfo,
)
from ai.backend.common.schema.deployment import IntOrPercent
from ai.backend.manager.api.gql.deployment.types.policy import (
    BlueGreenStrategySpecGQL,
    DeploymentPolicyGQL,
    RollingUpdateStrategySpecGQL,
)
from ai.backend.manager.api.gql.notification.types import (
    EmailSpecGQL,
    NotificationChannel,
    WebhookSpecGQL,
)
from ai.backend.manager.api.gql.schema import schema


def _object_type(name: str) -> GraphQLObjectType:
    graphql_type = schema._schema.get_type(name)
    assert isinstance(graphql_type, GraphQLObjectType), f"{name} is not an object type"
    return graphql_type


def _channel(spec: NotificationChannelSpecInfo) -> NotificationChannelNode:
    now = datetime.now(UTC)
    channel_id = uuid4()
    return NotificationChannelNode(
        id=channel_id,
        entity_id=channel_id,
        name="ops-channel",
        channel_type=spec.channel_type,
        spec=spec,
        enabled=True,
        created_at=now,
        created_by=uuid4(),
        updated_at=now,
    )


def _policy(spec: DeploymentStrategySpecInfo) -> DeploymentPolicyNode:
    now = datetime.now(UTC)
    policy_id = uuid4()
    return DeploymentPolicyNode(
        id=policy_id,
        field_id=policy_id,
        deployment_id=uuid4(),
        strategy_spec=spec,
        created_at=now,
        updated_at=now,
    )


class TestSpecTypesInSchema:
    @pytest.mark.parametrize(
        ("type_name", "fields"),
        [
            ("NotificationChannelSpec", ["channelType", "webhook", "email"]),
            ("DeploymentStrategySpec", ["strategy", "rollingUpdate", "blueGreen"]),
        ],
    )
    def test_the_spec_is_an_object_with_one_field_per_kind(
        self, type_name: str, fields: list[str]
    ) -> None:
        graphql_type = _object_type(type_name)

        assert list(graphql_type.fields) == fields
        assert not graphql_type.interfaces

    @pytest.mark.parametrize(
        ("type_name", "field"),
        [
            ("WebhookSpec", "url"),
            ("EmailSpec", "smtp"),
            ("RollingUpdateStrategySpec", "maxSurge"),
            ("BlueGreenStrategySpec", "autoPromote"),
        ],
    )
    def test_the_concrete_spec_is_a_plain_object(self, type_name: str, field: str) -> None:
        graphql_type = _object_type(type_name)

        assert field in graphql_type.fields
        assert not graphql_type.interfaces

    @pytest.mark.parametrize(
        ("type_name", "field"),
        [
            ("NotificationChannelSpec", "webhook"),
            ("NotificationChannelSpec", "email"),
            ("DeploymentStrategySpec", "rollingUpdate"),
            ("DeploymentStrategySpec", "blueGreen"),
        ],
    )
    def test_a_new_spec_field_carries_its_added_version(self, type_name: str, field: str) -> None:
        description = _object_type(type_name).fields[field].description

        assert description is not None
        assert description.startswith("Added in ")

    def test_the_email_spec_exposes_no_smtp_password(self) -> None:
        assert list(_object_type("SMTPAuth").fields) == ["username"]


class TestChannelSpecConversion:
    def test_a_webhook_channel_sets_webhook_only(self) -> None:
        node = _channel(
            NotificationChannelSpecInfo(
                channel_type=NotificationChannelTypeDTO.WEBHOOK,
                webhook=WebhookSpecInfo(url="https://hooks.example.com/demo"),
            )
        )

        spec = NotificationChannel.from_pydantic(node).spec

        assert spec.channel_type == NotificationChannelTypeDTO.WEBHOOK
        assert isinstance(spec.webhook, WebhookSpecGQL)
        assert spec.webhook.url == "https://hooks.example.com/demo"
        assert spec.email is None

    def test_an_email_channel_sets_email_only(self) -> None:
        node = _channel(
            NotificationChannelSpecInfo(
                channel_type=NotificationChannelTypeDTO.EMAIL,
                email=EmailSpecInfo(
                    smtp=SMTPConnectionInfo(
                        host="smtp.example.com", port=587, use_tls=True, timeout=30
                    ),
                    message=EmailMessageInfo(
                        from_email="ops@example.com", to_emails=["team@example.com"]
                    ),
                    auth=SMTPAuthInfo(username="ops"),
                ),
            )
        )

        spec = NotificationChannel.from_pydantic(node).spec

        assert spec.channel_type == NotificationChannelTypeDTO.EMAIL
        assert spec.webhook is None
        assert isinstance(spec.email, EmailSpecGQL)
        assert spec.email.smtp.host == "smtp.example.com"
        assert spec.email.message.to_emails == ["team@example.com"]
        assert spec.email.auth is not None
        assert spec.email.auth.username == "ops"


class TestStrategySpecConversion:
    def test_a_rolling_policy_sets_rolling_update_only(self) -> None:
        node = _policy(
            DeploymentStrategySpecInfo(
                strategy=DeploymentStrategy.ROLLING,
                rolling_update=RollingUpdateStrategySpecInfo(
                    max_surge=IntOrPercent(count=1),
                    max_unavailable=IntOrPercent(percent=0.25),
                ),
            )
        )

        spec = DeploymentPolicyGQL.from_pydantic(node).strategy_spec

        assert spec.strategy == DeploymentStrategy.ROLLING
        assert isinstance(spec.rolling_update, RollingUpdateStrategySpecGQL)
        assert spec.rolling_update.max_surge.count == 1
        assert spec.rolling_update.max_unavailable.percent == 0.25
        assert spec.blue_green is None

    def test_a_blue_green_policy_sets_blue_green_only(self) -> None:
        node = _policy(
            DeploymentStrategySpecInfo(
                strategy=DeploymentStrategy.BLUE_GREEN,
                blue_green=BlueGreenStrategySpecInfo(auto_promote=True, promote_delay_seconds=30),
            )
        )

        spec = DeploymentPolicyGQL.from_pydantic(node).strategy_spec

        assert spec.strategy == DeploymentStrategy.BLUE_GREEN
        assert spec.rolling_update is None
        assert isinstance(spec.blue_green, BlueGreenStrategySpecGQL)
        assert spec.blue_green.auto_promote is True
        assert spec.blue_green.promote_delay_seconds == 30
