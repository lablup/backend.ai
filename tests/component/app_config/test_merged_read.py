"""Component tests for the merged AppConfig REST v2 read.

The merge rules themselves are verified in the service and repository unit tests and are
not re-asserted here.
"""

from __future__ import annotations

import pytest

from ai.backend.client.v2.exceptions import AuthenticationError
from ai.backend.client.v2.v2_registry import V2ClientRegistry
from ai.backend.common.dto.manager.v2.app_config.request import (
    MyGetAppConfigsInput,
    PublicGetAppConfigsInput,
)


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
        """The principal on the request reaches the query: the caller's own fragment overrides
        the public one, and a key only the public fragment carries still survives."""
        result = await user_v2_registry.app_config.my_get_app_configs(
            MyGetAppConfigsInput(config_names=["contributed"])
        )

        merged = result.app_configs[0]
        assert merged.config == {"mode": "dark", "lang": "en"}

    async def test_the_public_read_sees_only_public_over_the_same_data(
        self,
        anonymous_v2_registry: V2ClientRegistry,
        merged_fragments: None,
    ) -> None:
        """Over the very same rows the anonymous caller sees the public fragment alone, so
        visibility follows who is asking rather than what is stored."""
        result = await anonymous_v2_registry.app_config.public_get_app_configs(
            PublicGetAppConfigsInput(config_names=["contributed"])
        )

        merged = result.app_configs[0]
        assert merged.config == {"mode": "light", "lang": "en"}
