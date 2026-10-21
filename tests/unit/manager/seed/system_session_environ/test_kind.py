"""The `system_session_environ` kind reads one item per variable and scope."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pytest

from ai.backend.manager.errors.seed import InvalidSeedDocument
from ai.backend.manager.seed.system_session_environ.seed import SystemSessionEnvironSeed

_DOMAIN_ID = "0198a5a0-0000-7000-8000-00000000d001"


@dataclass(frozen=True)
class _KeyCase:
    name: str
    item: dict[str, Any]
    expected: str


@dataclass(frozen=True)
class _InvalidItemCase:
    name: str
    item: dict[str, Any]


class TestSystemSessionEnvironSeed:
    @pytest.mark.parametrize(
        "case",
        [
            _KeyCase(
                name="public",
                item={
                    "value_source": "session_id",
                    "key": "BACKENDAI_SESSION_ID",
                    "scope_type": "public",
                    "enabled": True,
                },
                expected="BACKENDAI_SESSION_ID:public",
            ),
            _KeyCase(
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
            _KeyCase(
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
    def test_the_key_names_the_variable_and_its_scope(self, case: _KeyCase) -> None:
        assert SystemSessionEnvironSeed.model_validate(case.item).key() == case.expected

    @pytest.mark.parametrize(
        "case",
        [
            _InvalidItemCase(
                name="missing-value-source",
                item={"key": "K", "scope_type": "public", "enabled": True},
            ),
            _InvalidItemCase(
                name="missing-key",
                item={"value_source": "session_id", "scope_type": "public", "enabled": True},
            ),
            _InvalidItemCase(
                name="missing-enabled",
                item={"value_source": "session_id", "key": "K", "scope_type": "public"},
            ),
            _InvalidItemCase(
                name="unknown-value-source",
                item={
                    "value_source": "hostname",
                    "key": "K",
                    "scope_type": "public",
                    "enabled": True,
                },
            ),
            _InvalidItemCase(
                name="key-not-an-environ-name",
                item={
                    "value_source": "session_id",
                    "key": "1BAD",
                    "scope_type": "public",
                    "enabled": True,
                },
            ),
            _InvalidItemCase(
                name="too-long-key",
                item={
                    "value_source": "session_id",
                    "key": "K" * 257,
                    "scope_type": "public",
                    "enabled": True,
                },
            ),
            _InvalidItemCase(
                name="unknown-scope-type",
                item={
                    "value_source": "session_id",
                    "key": "K",
                    "scope_type": "user",
                    "enabled": True,
                },
            ),
            _InvalidItemCase(
                name="public-with-scope-id",
                item={
                    "value_source": "session_id",
                    "key": "K",
                    "scope_type": "public",
                    "scope_id": _DOMAIN_ID,
                    "enabled": True,
                },
            ),
            _InvalidItemCase(
                name="domain-without-scope-id",
                item={
                    "value_source": "session_id",
                    "key": "K",
                    "scope_type": "domain",
                    "enabled": True,
                },
            ),
            _InvalidItemCase(
                name="project-without-scope-id",
                item={
                    "value_source": "session_id",
                    "key": "K",
                    "scope_type": "project",
                    "enabled": True,
                },
            ),
            _InvalidItemCase(
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
    def test_an_invalid_item_is_refused(self, case: _InvalidItemCase) -> None:
        with pytest.raises(InvalidSeedDocument):
            SystemSessionEnvironSeed.model_validate(case.item)
