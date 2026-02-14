from collections.abc import Mapping
from datetime import datetime

import pytest
from yarl import URL

from ai.backend.client.v2.auth import AuthStrategy
from ai.backend.client.v2.config import ClientConfig


class MockAuth(AuthStrategy):
    """A mock auth strategy for testing that returns predictable headers."""

    def sign(
        self,
        method: str,
        version: str,
        endpoint: URL,
        date: datetime,
        rel_url: str,
        content_type: str,
    ) -> Mapping[str, str]:
        return {"Authorization": "BackendAI signMethod=HMAC-SHA256, credential=mock:mock_sig"}


@pytest.fixture
def mock_auth() -> AuthStrategy:
    return MockAuth()


@pytest.fixture
def sample_config() -> ClientConfig:
    return ClientConfig(endpoint=URL("https://api.example.com"))
