"""Component tests for the merged AppConfig REST v2 read.

Which scopes a reader may draw from, and what the merge does where two of them hold the same
key, read off the response the client actually receives. Rank ordering itself — which scope
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


@dataclass(frozen=True)
class _MergeCase:
    """The fragment each scope holds, and what ``key`` merges to in the caller's read.

    ``None`` for a scope writes no fragment there; ``{}`` writes one carrying no key. Neither
    is the same as a fragment whose value for the key *is* ``null``, which is its own rule.
    """

    description: str
    key: str
    public: dict[str, Any] | None
    domain: dict[str, Any] | None
    user: dict[str, Any] | None
    expected: Any


class TestMergedRead:
    async def test_the_authenticated_read_turns_away_a_caller_with_no_credentials(
        self,
        anonymous_v2_registry: V2ClientRegistry,
    ) -> None:
        """Only its public sibling is reachable unauthenticated, which the merge test relies on
        by reading through the very same credential-less client."""
        with pytest.raises(AuthenticationError):
            await anonymous_v2_registry.app_config.my_get_app_configs(
                MyGetAppConfigsInput(config_names=["anything"])
            )

    @pytest.mark.parametrize(
        "case",
        [
            _MergeCase(
                description="nested objects merge recursively",
                key="theme",
                public={"theme": {"mode": "light"}},
                domain={"theme": {"accent": "teal"}},
                user={"theme": {"font": "mono"}},
                expected={"mode": "light", "accent": "teal", "font": "mono"},
            ),
            _MergeCase(
                description="a scalar is replaced by the highest rank that carries it",
                key="mode",
                public={"mode": "light"},
                domain={"mode": "solarized"},
                user={"mode": "dark"},
                expected="dark",
            ),
            _MergeCase(
                description="a list is replaced whole, neither blended nor appended to",
                key="pinned",
                public={"pinned": ["home", "docs", "support"]},
                domain={"pinned": ["home", "wiki"]},
                user={"pinned": ["home"]},
                expected=["home"],
            ),
            _MergeCase(
                description="an explicit null erases what was inherited",
                key="banner",
                public={"banner": "Welcome"},
                domain={"banner": "Compliance notice"},
                user={"banner": None},
                expected=None,
            ),
            _MergeCase(
                description="a key the higher scopes omit keeps the inherited value",
                key="lang",
                public={"lang": "en"},
                domain={},
                user={},
                expected="en",
            ),
        ],
        ids=lambda case: case.description,
    )
    async def test_the_merge_follows_its_rule(
        self,
        seed_colliding_fragments: SeedFragments,
        user_v2_registry: V2ClientRegistry,
        case: _MergeCase,
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

        assert result.app_configs[0].config[case.key] == case.expected

    async def test_the_public_read_draws_from_the_public_scope_alone(
        self,
        seed_colliding_fragments: SeedFragments,
        anonymous_v2_registry: V2ClientRegistry,
    ) -> None:
        """Over rows the caller would merge all three of, the public read answers with one."""
        config_name = await seed_colliding_fragments({
            AppConfigScopeType.PUBLIC: {"mode": "light"},
            AppConfigScopeType.DOMAIN: {"mode": "solarized"},
            AppConfigScopeType.USER: {"mode": "dark"},
        })

        result = await anonymous_v2_registry.app_config.public_get_app_configs(
            PublicGetAppConfigsInput(config_names=[config_name])
        )

        assert result.app_configs[0].config["mode"] == "light"
