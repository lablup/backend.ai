"""Component tests for the merged AppConfig REST v2 read.

Which scopes a caller may draw from, and what the merge does where two of them collide,
read off the response the client actually receives. Rank ordering itself — which scope
overrides which — is asserted in the service and repository unit tests.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pytest

from ai.backend.client.v2.exceptions import AuthenticationError
from ai.backend.client.v2.v2_registry import V2ClientRegistry
from ai.backend.common.data.app_config.types import AppConfigScopeType
from ai.backend.common.dto.manager.v2.app_config.request import (
    MyGetAppConfigsInput,
    PublicGetAppConfigsInput,
)

from .conftest import SeedFragments


class TestMergedRead:
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


class TestVisibilityFollowsTheCaller:
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


@dataclass(frozen=True)
class _CollisionCase:
    """The config each scope's fragment holds, and what the caller's read merges out of them.

    ``None`` for a scope writes no fragment there; ``{}`` writes one that carries no key. The
    two differ from a fragment whose value for the key *is* ``null``, which is its own rule.
    """

    description: str
    public: dict[str, Any] | None
    domain: dict[str, Any] | None
    user: dict[str, Any] | None
    expected: Any


class TestKeyCollision:
    """What each value kind does where the scopes a caller can see hold the same key."""

    @pytest.mark.parametrize(
        "case",
        [
            _CollisionCase(
                description="nested objects merge recursively",
                public={"key": {"from_public": 1}},
                domain={"key": {"from_domain": 2}},
                user={"key": {"from_user": 3}},
                expected={"from_public": 1, "from_domain": 2, "from_user": 3},
            ),
            _CollisionCase(
                description="a scalar is replaced by the highest rank that carries it",
                public={"key": "public"},
                domain={"key": "domain"},
                user={"key": "user"},
                expected="user",
            ),
            _CollisionCase(
                description="a list is replaced whole, neither blended nor appended to",
                public={"key": ["a", "b", "c"]},
                domain=None,
                user={"key": ["a"]},
                expected=["a"],
            ),
            _CollisionCase(
                description="an explicit null erases what was inherited",
                public={"key": "public"},
                domain=None,
                user={"key": None},
                expected=None,
            ),
            _CollisionCase(
                description="a key the higher scopes omit keeps the inherited value",
                public={"key": "public"},
                domain={},
                user={},
                expected="public",
            ),
        ],
        ids=lambda case: case.description,
    )
    async def test_the_merge_follows_its_rule(
        self,
        seed_colliding_fragments: SeedFragments,
        user_v2_registry: V2ClientRegistry,
        case: _CollisionCase,
    ) -> None:
        """Subscripting rather than ``.get`` on purpose: a key the merge dropped is a failure,
        which is what separates the null case from the omitted one."""
        config_name = await seed_colliding_fragments({
            AppConfigScopeType.PUBLIC: case.public,
            AppConfigScopeType.DOMAIN: case.domain,
            AppConfigScopeType.USER: case.user,
        })

        result = await user_v2_registry.app_config.my_get_app_configs(
            MyGetAppConfigsInput(config_names=[config_name])
        )

        assert result.app_configs[0].config["key"] == case.expected
