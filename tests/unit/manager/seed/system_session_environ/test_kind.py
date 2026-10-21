"""The `system_session_environ` kind reads one item per variable and scope."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pytest

from ai.backend.manager.errors.seed import InvalidSeedDocument
from ai.backend.manager.seed.system_session_environ.seed import SystemSessionEnvironSeed

_DOMAIN_ID = "0198a5a0-0000-7000-8000-00000000d001"


@dataclass(frozen=True)
class _SeedKeyCase:
    name: str
    item: dict[str, Any]
    expected: str


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
                item={
                    "value_source": "session_id",
                    "key": "BACKENDAI_SESSION_ID",
                    "scope_type": "public",
                    "enabled": True,
                },
                expected="BACKENDAI_SESSION_ID:public",
            ),
            _SeedKeyCase(
                name="domain",
                item={
                    "value_source": "session_id",
                    "key": "BACKENDAI_SESSION_ID",
                    "scope_type": "domain",
                    "scope_id": _DOMAIN_ID,
                    "enabled": True,
                },
                expected=f"BACKENDAI_SESSION_ID:domain:{_DOMAIN_ID}",
            ),
            _SeedKeyCase(
                name="project",
                item={
                    "value_source": "session_id",
                    "key": "BACKENDAI_SESSION_ID",
                    "scope_type": "project",
                    "scope_id": _DOMAIN_ID,
                    "enabled": True,
                },
                expected=f"BACKENDAI_SESSION_ID:project:{_DOMAIN_ID}",
            ),
        ],
        ids=lambda case: case.name,
    )
    def test_the_key_names_the_variable_and_its_scope(self, case: _SeedKeyCase) -> None:
        assert SystemSessionEnvironSeed.model_validate(case.item).key() == case.expected

    @pytest.mark.parametrize(
        "case",
        [
            _InvalidSeedItemCase(
                name="missing-value-source",
                item={"key": "K", "scope_type": "public", "enabled": True},
            ),
            _InvalidSeedItemCase(
                name="missing-key",
                item={"value_source": "session_id", "scope_type": "public", "enabled": True},
            ),
            _InvalidSeedItemCase(
                name="missing-enabled",
                item={"value_source": "session_id", "key": "K", "scope_type": "public"},
            ),
            _InvalidSeedItemCase(
                name="unknown-value-source",
                item={
                    "value_source": "hostname",
                    "key": "K",
                    "scope_type": "public",
                    "enabled": True,
                },
            ),
            _InvalidSeedItemCase(
                name="key-not-an-environ-name",
                item={
                    "value_source": "session_id",
                    "key": "1BAD",
                    "scope_type": "public",
                    "enabled": True,
                },
            ),
            _InvalidSeedItemCase(
                name="too-long-key",
                item={
                    "value_source": "session_id",
                    "key": "K" * 257,
                    "scope_type": "public",
                    "enabled": True,
                },
            ),
            _InvalidSeedItemCase(
                name="unknown-scope-type",
                item={
                    "value_source": "session_id",
                    "key": "K",
                    "scope_type": "user",
                    "enabled": True,
                },
            ),
            _InvalidSeedItemCase(
                name="public-with-scope-id",
                item={
                    "value_source": "session_id",
                    "key": "K",
                    "scope_type": "public",
                    "scope_id": _DOMAIN_ID,
                    "enabled": True,
                },
            ),
            _InvalidSeedItemCase(
                name="domain-without-scope-id",
                item={
                    "value_source": "session_id",
                    "key": "K",
                    "scope_type": "domain",
                    "enabled": True,
                },
            ),
            _InvalidSeedItemCase(
                name="project-without-scope-id",
                item={
                    "value_source": "session_id",
                    "key": "K",
                    "scope_type": "project",
                    "enabled": True,
                },
            ),
            _InvalidSeedItemCase(
                name="unknown-field",
                item={
                    "value_source": "session_id",
                    "key": "K",
                    "scope_type": "public",
                    "enabled": True,
                    "rank": 1,
                },
            ),
        ],
        ids=lambda case: case.name,
    )
    def test_an_invalid_item_is_refused(self, case: _InvalidSeedItemCase) -> None:
        with pytest.raises(InvalidSeedDocument):
            SystemSessionEnvironSeed.model_validate(case.item)
