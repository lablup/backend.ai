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
    """The fragment each scope holds for one config name, and the config the caller reads.

    ``None`` for a scope writes no fragment there; ``{}`` writes one carrying no key. Neither
    is the same as a fragment whose value for a key *is* ``null``, which is its own rule.
    """

    description: str
    config_name: str
    public: dict[str, Any] | None
    domain: dict[str, Any] | None
    user: dict[str, Any] | None
    expected: dict[str, Any]


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
                config_name="theme",
                public={"palette": {"mode": "light"}},
                domain={"palette": {"accent": "teal"}},
                user={"palette": {"font": "mono"}},
                expected={"palette": {"mode": "light", "accent": "teal", "font": "mono"}},
            ),
            _MergeCase(
                description="a scalar is replaced by the highest rank that carries it",
                config_name="theme",
                public={"mode": "light"},
                domain={"mode": "solarized"},
                user={"mode": "dark"},
                expected={"mode": "dark"},
            ),
            _MergeCase(
                description="a list is replaced whole, neither blended nor appended to",
                config_name="menu",
                public={"pinned": ["home", "docs", "support"]},
                domain={"pinned": ["home", "wiki"]},
                user={"pinned": ["home"]},
                expected={"pinned": ["home"]},
            ),
            _MergeCase(
                description="an explicit null erases what was inherited",
                config_name="banner",
                public={"text": "Welcome"},
                domain={"text": "Compliance notice"},
                user={"text": None},
                expected={"text": None},
            ),
            _MergeCase(
                description="a key the higher scopes omit keeps the inherited value",
                config_name="locale",
                public={"lang": "en"},
                domain={},
                user={},
                expected={"lang": "en"},
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
        """Whole-config equality on purpose: the null case's key must come back as ``null``
        rather than disappear, which is what separates it from the omitted one."""
        await seed_colliding_fragments(
            case.config_name,
            {
                AppConfigScopeType.PUBLIC: case.public,
                AppConfigScopeType.DOMAIN: case.domain,
                AppConfigScopeType.USER: case.user,
            },
        )

        result = await user_v2_registry.app_config.my_get_app_configs(
            MyGetAppConfigsInput(config_names=[case.config_name])
        )

        assert result.app_configs[0].config == case.expected

    async def test_the_public_read_draws_from_the_public_scope_alone(
        self,
        seed_colliding_fragments: SeedFragments,
        anonymous_v2_registry: V2ClientRegistry,
    ) -> None:
        """Over rows the caller would merge all three of, the public read answers with one."""
        await seed_colliding_fragments(
            "theme",
            {
                AppConfigScopeType.PUBLIC: {"mode": "light"},
                AppConfigScopeType.DOMAIN: {"mode": "solarized"},
                AppConfigScopeType.USER: {"mode": "dark"},
            },
        )

        result = await anonymous_v2_registry.app_config.public_get_app_configs(
            PublicGetAppConfigsInput(config_names=["theme"])
        )

        assert result.app_configs[0].config == {"mode": "light"}
