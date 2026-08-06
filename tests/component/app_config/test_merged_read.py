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
    """The fragment each scope holds, and the value the caller's read merges out of them.

    ``None`` for a scope writes no fragment there; ``{}`` writes one carrying no key. Neither
    is the same as a fragment whose value for the key *is* ``null``, which is its own rule.
    """

    description: str
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
                public={"key": {"from_public": 1}},
                domain={"key": {"from_domain": 2}},
                user={"key": {"from_user": 3}},
                expected={"from_public": 1, "from_domain": 2, "from_user": 3},
            ),
            _MergeCase(
                description="a scalar is replaced by the highest rank that carries it",
                public={"key": "public"},
                domain={"key": "domain"},
                user={"key": "user"},
                expected="user",
            ),
            _MergeCase(
                description="a list is replaced whole, neither blended nor appended to",
                public={"key": ["a", "b", "c"]},
                domain=None,
                user={"key": ["a"]},
                expected=["a"],
            ),
            _MergeCase(
                description="an explicit null erases what was inherited",
                public={"key": "public"},
                domain=None,
                user={"key": None},
                expected=None,
            ),
            _MergeCase(
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

        assert result.app_configs[0].config["key"] == case.expected

    async def test_the_public_read_draws_from_the_public_scope_alone(
        self,
        seed_colliding_fragments: SeedFragments,
        anonymous_v2_registry: V2ClientRegistry,
    ) -> None:
        """Over rows the caller would merge all three of, the public read answers with one."""
        config_name = await seed_colliding_fragments({
            AppConfigScopeType.PUBLIC: {"key": "public"},
            AppConfigScopeType.DOMAIN: {"key": "domain"},
            AppConfigScopeType.USER: {"key": "user"},
        })

        result = await anonymous_v2_registry.app_config.public_get_app_configs(
            PublicGetAppConfigsInput(config_names=[config_name])
        )

        assert result.app_configs[0].config["key"] == "public"
