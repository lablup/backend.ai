"""The `system_session_environ` kind reads one item per variable and scope."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import UUID

import pytest

from ai.backend.common.data.entity.system_session_environ import SystemSessionEnvironScopeID
from ai.backend.common.data.system_session_environ.types import (
    SystemSessionEnvironScopeType,
    SystemSessionEnvironValueSource,
)
from ai.backend.manager.errors.seed import InvalidSeedDocument
from ai.backend.manager.seed.system_session_environ.seed import SystemSessionEnvironSeed

_DOMAIN_ID = "0198a5a0-0000-7000-8000-00000000d001"


@dataclass(frozen=True)
class _SeedKeyCase:
    name: str
    seed: SystemSessionEnvironSeed
    expected_key: str


@dataclass(frozen=True)
class _InvalidSeedItemCase:
    name: str
    item: dict[str, Any]


class TestSystemSessionEnvironSeed:
    @pytest.mark.parametrize(
        "case",
        [
            _SeedKeyCase(
                name="public",
                seed=SystemSessionEnvironSeed(
                    value_source=SystemSessionEnvironValueSource.SESSION_ID,
                    key="BACKENDAI_SESSION_ID",
                    scope_type=SystemSessionEnvironScopeType.PUBLIC,
                ),
                expected_key="BACKENDAI_SESSION_ID:public",
            ),
            _SeedKeyCase(
                name="domain",
                seed=SystemSessionEnvironSeed(
                    value_source=SystemSessionEnvironValueSource.SESSION_ID,
                    key="BACKENDAI_SESSION_ID",
                    scope_type=SystemSessionEnvironScopeType.DOMAIN,
                    scope_id=SystemSessionEnvironScopeID(UUID(_DOMAIN_ID)),
                ),
                expected_key=f"BACKENDAI_SESSION_ID:domain:{_DOMAIN_ID}",
            ),
            _SeedKeyCase(
                name="project",
                seed=SystemSessionEnvironSeed(
                    value_source=SystemSessionEnvironValueSource.SESSION_ID,
                    key="BACKENDAI_SESSION_ID",
                    scope_type=SystemSessionEnvironScopeType.PROJECT,
                    scope_id=SystemSessionEnvironScopeID(UUID(_DOMAIN_ID)),
                ),
                expected_key=f"BACKENDAI_SESSION_ID:project:{_DOMAIN_ID}",
            ),
        ],
        ids=lambda case: case.name,
    )
    def test_the_key_names_the_variable_and_its_scope(self, case: _SeedKeyCase) -> None:
        assert case.seed.key() == case.expected_key

    @pytest.mark.parametrize(
        "case",
        [
            _InvalidSeedItemCase(
                name="missing-value-source",
                item={"key": "K", "scope_type": "public"},
            ),
            _InvalidSeedItemCase(
                name="missing-key",
                item={"value_source": "session_id", "scope_type": "public"},
            ),
            _InvalidSeedItemCase(
                name="unknown-value-source",
                item={
                    "value_source": "hostname",
                    "key": "K",
                    "scope_type": "public",
                },
            ),
            _InvalidSeedItemCase(
                name="key-not-an-environ-name",
                item={
                    "value_source": "session_id",
                    "key": "1BAD",
                    "scope_type": "public",
                },
            ),
            _InvalidSeedItemCase(
                name="too-long-key",
                item={
                    "value_source": "session_id",
                    "key": "K" * 257,
                    "scope_type": "public",
                },
            ),
            _InvalidSeedItemCase(
                name="unknown-scope-type",
                item={
                    "value_source": "session_id",
                    "key": "K",
                    "scope_type": "user",
                },
            ),
            _InvalidSeedItemCase(
                name="public-with-scope-id",
                item={
                    "value_source": "session_id",
                    "key": "K",
                    "scope_type": "public",
                    "scope_id": _DOMAIN_ID,
                },
            ),
            _InvalidSeedItemCase(
                name="domain-without-scope-id",
                item={
                    "value_source": "session_id",
                    "key": "K",
                    "scope_type": "domain",
                },
            ),
            _InvalidSeedItemCase(
                name="project-without-scope-id",
                item={
                    "value_source": "session_id",
                    "key": "K",
                    "scope_type": "project",
                },
            ),
            _InvalidSeedItemCase(
                name="unknown-field",
                item={
                    "value_source": "session_id",
                    "key": "K",
                    "scope_type": "public",
                    "rank": 1,
                },
            ),
        ],
        ids=lambda case: case.name,
    )
    def test_an_invalid_item_is_refused(self, case: _InvalidSeedItemCase) -> None:
        with pytest.raises(InvalidSeedDocument):
            SystemSessionEnvironSeed.model_validate(case.item)
