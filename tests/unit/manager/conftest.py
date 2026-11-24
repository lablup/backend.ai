from __future__ import annotations

import secrets

import pytest

pytest_plugins = [
    "ai.backend.testutils.bootstrap",
    "ai.backend.testutils.db_fixtures",
    "ai.backend.testutils.otel",
]


@pytest.fixture(scope="session", autouse=True)
def test_id() -> str:
    return secrets.token_hex(12)


@pytest.fixture(scope="session", autouse=True)
def test_ns(test_id: str) -> str:
    return f"testing-ns-{test_id}"
