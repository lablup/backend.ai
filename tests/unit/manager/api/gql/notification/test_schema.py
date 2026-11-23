"""Interface implementors the v2 GraphQL schema must expose so clients can read their fields."""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from graphql import GraphQLObjectType, GraphQLResolveInfo

from ai.backend.common.dto.manager.v2.notification.response import NotificationChannelNode
from ai.backend.common.dto.manager.v2.notification.types import (
    NotificationChannelTypeDTO,
    WebhookSpecInfo,
)
from ai.backend.manager.api.gql.notification.types import NotificationChannel, WebhookSpecGQL
from ai.backend.manager.api.gql.schema import schema


def _object_type(name: str) -> GraphQLObjectType:
    graphql_type = schema._schema.get_type(name)
    assert isinstance(graphql_type, GraphQLObjectType), f"{name} is not an object type"
    return graphql_type


class TestInterfaceImplementorsAreRegistered:
    @pytest.mark.parametrize(
        ("implementor", "interface", "field"),
        [
            ("WebhookSpec", "NotificationChannelSpec", "url"),
            ("EmailSpec", "NotificationChannelSpec", "smtp"),
            ("RollingUpdateStrategySpec", "DeploymentStrategySpec", "maxSurge"),
            ("BlueGreenStrategySpec", "DeploymentStrategySpec", "autoPromote"),
        ],
    )
    def test_the_implementor_and_its_fields_are_in_the_schema(
        self, implementor: str, interface: str, field: str
    ) -> None:
        graphql_type = _object_type(implementor)

        assert [i.name for i in graphql_type.interfaces] == [interface]
        assert field in graphql_type.fields

    def test_the_email_spec_exposes_no_smtp_password(self) -> None:
        assert list(_object_type("SMTPAuth").fields) == ["username"]


class TestChannelSpecResolvesToItsImplementor:
    def test_a_webhook_channel_spec_becomes_the_webhook_spec_type(self) -> None:
        now = datetime.now(UTC)
        channel_id = uuid4()
        node = NotificationChannelNode(
            id=channel_id,
            entity_id=channel_id,
            name="ops-webhook",
            channel_type=NotificationChannelTypeDTO.WEBHOOK,
            spec=WebhookSpecInfo(
                channel_type=NotificationChannelTypeDTO.WEBHOOK,
                url="https://hooks.example.com/demo",
            ),
            enabled=True,
            created_at=now,
            created_by=uuid4(),
            updated_at=now,
        )

        spec = NotificationChannel.from_pydantic(node).spec

        assert isinstance(spec, WebhookSpecGQL)
        assert spec.url == "https://hooks.example.com/demo"
        is_type_of = _object_type("WebhookSpec").is_type_of
        assert is_type_of is not None
        assert is_type_of(spec, MagicMock(spec=GraphQLResolveInfo))
