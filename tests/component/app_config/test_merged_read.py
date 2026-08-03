"""Component tests for the merged AppConfig REST v2 read.

Covers what only shows at the HTTP boundary: that the public route reaches the handler with
no credentials while its authenticated sibling still rejects the same caller, and that the
merged payload serializes. The merge itself is verified in the service and repository unit
tests and is not re-asserted here.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import TYPE_CHECKING

import pytest
import yarl

from ai.backend.client.v2.auth import HMACAuth, NoAuth
from ai.backend.client.v2.config import ClientConfig
from ai.backend.client.v2.exceptions import AuthenticationError
from ai.backend.client.v2.v2_registry import V2ClientRegistry
from ai.backend.common.dto.manager.v2.app_config.request import (
    MyGetAppConfigsInput,
    PublicGetAppConfigsInput,
)

if TYPE_CHECKING:
    from tests.component.conftest import ServerInfo, UserFixtureData


@pytest.fixture()
async def user_v2_registry(
    server: ServerInfo,
    regular_user_fixture: UserFixtureData,
) -> AsyncIterator[V2ClientRegistry]:
    registry = await V2ClientRegistry.create(
        ClientConfig(endpoint=yarl.URL(server.url)),
        HMACAuth(
            access_key=regular_user_fixture.keypair.access_key,
            secret_key=regular_user_fixture.keypair.secret_key,
        ),
    )
    try:
        yield registry
    finally:
        await registry.close()


@pytest.fixture()
async def anonymous_v2_registry(server: ServerInfo) -> AsyncIterator[V2ClientRegistry]:
    """A caller that holds no credentials at all — the pre-login client."""
    registry = await V2ClientRegistry.create(ClientConfig(endpoint=yarl.URL(server.url)), NoAuth())
    try:
        yield registry
    finally:
        await registry.close()


class TestAnonymousReach:
    async def test_public_read_answers_a_caller_with_no_credentials(
        self,
        anonymous_v2_registry: V2ClientRegistry,
        merged_fragments: None,
    ) -> None:
        """The route carries no auth middleware, so the request must reach the handler."""
        result = await anonymous_v2_registry.app_config.public_get_app_configs(
            PublicGetAppConfigsInput(config_names=["contributed"])
        )

        assert [node.config_name for node in result.app_configs] == ["contributed"]

    async def test_authenticated_read_rejects_the_same_caller(
        self,
        anonymous_v2_registry: V2ClientRegistry,
        merged_fragments: None,
    ) -> None:
        """Its sibling route is still gated — the public one is the only way in unauthenticated."""
        with pytest.raises(AuthenticationError):
            await anonymous_v2_registry.app_config.my_get_app_configs(
                MyGetAppConfigsInput(config_names=["contributed"])
            )


class TestPrincipalDecidesTheMerge:
    async def test_the_authenticated_read_carries_the_callers_own_overlay(
        self,
        user_v2_registry: V2ClientRegistry,
        merged_fragments: None,
    ) -> None:
        result = await user_v2_registry.app_config.my_get_app_configs(
            MyGetAppConfigsInput(config_names=["contributed"])
        )

        merged = result.app_configs[0]
        assert merged.merged_config == {"mode": "dark", "lang": "en"}
        assert len(merged.fragments) == 2

    async def test_the_public_read_sees_only_public_over_the_same_data(
        self,
        anonymous_v2_registry: V2ClientRegistry,
        merged_fragments: None,
    ) -> None:
        result = await anonymous_v2_registry.app_config.public_get_app_configs(
            PublicGetAppConfigsInput(config_names=["contributed"])
        )

        merged = result.app_configs[0]
        assert merged.merged_config == {"mode": "light", "lang": "en"}
        assert len(merged.fragments) == 1


class TestPayloadShape:
    async def test_an_uncontributed_name_serializes_as_an_empty_merge(
        self,
        user_v2_registry: V2ClientRegistry,
        merged_fragments: None,
    ) -> None:
        """A name nothing contributes to holds its place instead of failing the response."""
        result = await user_v2_registry.app_config.my_get_app_configs(
            MyGetAppConfigsInput(config_names=["contributed", "uncontributed"])
        )

        assert [node.config_name for node in result.app_configs] == [
            "contributed",
            "uncontributed",
        ]
        uncontributed = result.app_configs[1]
        assert uncontributed.merged_config == {}
        assert uncontributed.fragments == []
