from collections.abc import Mapping
from datetime import datetime
from typing import override
from uuid import UUID, uuid4

import pytest
from yarl import URL

from ai.backend.client.v2.auth import AuthStrategy


class MockAuth(AuthStrategy):
    """A mock auth strategy for testing that returns predictable headers."""

    @override
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
def sample_client_type_id() -> UUID:
    return uuid4()
