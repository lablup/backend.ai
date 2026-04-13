"""Tests for V2GQLClient._gql_path() and URL construction."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from yarl import URL

from ai.backend.client.v2.base_client import BackendAIAuthClient
from ai.backend.client.v2.config import ClientConfig
from ai.backend.client.v2.domains_v2.gql import V2GQLClient


@pytest.fixture
def session_config() -> ClientConfig:
    return ClientConfig(endpoint=URL("http://localhost:8090"), endpoint_type="session")


@pytest.fixture
def api_config() -> ClientConfig:
    return ClientConfig(endpoint=URL("http://localhost:8090"), endpoint_type="api")


def _make_gql_client(config: ClientConfig) -> V2GQLClient:
    mock_client = MagicMock(spec=BackendAIAuthClient)
    mock_client._config = config
    return V2GQLClient(mock_client)


class TestV2GQLClientPath:
    """Verify _gql_path() x _build_url() produce correct final URLs."""

    def test_session_v2_url(self, session_config: ClientConfig) -> None:
        gql = _make_gql_client(session_config)
        path = gql._gql_path(v2=True)
        url = BackendAIAuthClient._build_url(MagicMock(_config=session_config), path)
        assert url == "http://localhost:8090/func/admin/gql"

    def test_session_legacy_url(self, session_config: ClientConfig) -> None:
        gql = _make_gql_client(session_config)
        path = gql._gql_path(v2=False)
        url = BackendAIAuthClient._build_url(MagicMock(_config=session_config), path)
        assert url == "http://localhost:8090/func/admin/gql"

    def test_api_v2_url(self, api_config: ClientConfig) -> None:
        gql = _make_gql_client(api_config)
        path = gql._gql_path(v2=True)
        url = BackendAIAuthClient._build_url(MagicMock(_config=api_config), path)
        assert url == "http://localhost:8090/admin/gql/strawberry"

    def test_api_legacy_url(self, api_config: ClientConfig) -> None:
        gql = _make_gql_client(api_config)
        path = gql._gql_path(v2=False)
        url = BackendAIAuthClient._build_url(MagicMock(_config=api_config), path)
        assert url == "http://localhost:8090/admin/gql"
