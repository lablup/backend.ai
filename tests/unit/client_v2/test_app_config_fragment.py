from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from yarl import URL

from ai.backend.client.v2.base_client import BackendAIAuthClient
from ai.backend.client.v2.config import ClientConfig
from ai.backend.client.v2.domains_v2.app_config_fragment import V2AppConfigFragmentClient
from ai.backend.common.data.app_config.types import AppConfigScopeType
from ai.backend.common.dto.manager.v2.app_config_fragment.request import (
    AdminSearchAppConfigFragmentInput,
    AppConfigFragmentUpsertItem,
    AppConfigScopeRef,
    BulkPurgeAppConfigFragmentInput,
    MyAppConfigFragmentsByNamesInput,
    MyPurgeAppConfigFragmentsByNamesInput,
    MyUpsertAppConfigFragmentsInput,
    ScopedAppConfigFragmentsByNamesInput,
    ScopedPurgeAppConfigFragmentsByNamesInput,
    ScopedUpsertAppConfigFragmentsInput,
)
from ai.backend.common.dto.manager.v2.app_config_fragment.response import (
    AppConfigFragmentNode,
    AppConfigFragmentsByNamesPayload,
    BulkPurgeAppConfigFragmentPayload,
    PurgeAppConfigFragmentPayload,
    PurgeAppConfigFragmentsByNamesPayload,
    SearchAppConfigFragmentPayload,
    UpsertAppConfigFragmentsPayload,
)
from ai.backend.common.identifier.app_config import AppConfigScopeID
from ai.backend.common.identifier.app_config_fragment import AppConfigFragmentID

from .conftest import MockAuth

_DEFAULT_CONFIG = ClientConfig(endpoint=URL("https://api.example.com"))
_USER_SCOPE_ID = uuid4()


@pytest.fixture
def fragment_id() -> AppConfigFragmentID:
    return AppConfigFragmentID(uuid4())


@pytest.fixture
def node_payload(fragment_id: AppConfigFragmentID) -> dict[str, Any]:
    """One fragment as the server sends it, for a ``theme`` fragment at a user scope."""
    return {
        "id": str(fragment_id),
        "config_name": "theme",
        "scope_type": "user",
        "scope_id": str(_USER_SCOPE_ID),
        "config": {"mode": "dark"},
        "created_at": "2026-01-01T00:00:00+00:00",
        "updated_at": "2026-01-02T00:00:00+00:00",
    }


@pytest.fixture
def mock_response() -> AsyncMock:
    """The HTTP response the mocked session hands back; each test sets its ``json``."""
    response = AsyncMock()
    response.status = 200
    return response


@pytest.fixture
def mock_session(mock_response: AsyncMock) -> MagicMock:
    request_ctx = AsyncMock()
    request_ctx.__aenter__ = AsyncMock(return_value=mock_response)
    request_ctx.__aexit__ = AsyncMock(return_value=False)
    session = MagicMock()
    session.request = MagicMock(return_value=request_ctx)
    return session


@pytest.fixture
def client(mock_session: MagicMock) -> V2AppConfigFragmentClient:
    return V2AppConfigFragmentClient(BackendAIAuthClient(_DEFAULT_CONFIG, MockAuth(), mock_session))


class TestScopedByNames:
    async def test_answers_one_entry_per_requested_name(
        self,
        client: V2AppConfigFragmentClient,
        mock_session: MagicMock,
        mock_response: AsyncMock,
        node_payload: dict[str, Any],
    ) -> None:
        """A name with no fragment at the scope holds its place as a null."""
        mock_response.json = AsyncMock(
            return_value=[node_payload, None],
        )

        result = await client.scoped_get_app_config_fragments_by_names(
            ScopedAppConfigFragmentsByNamesInput(
                scope=AppConfigScopeRef(
                    scope_type=AppConfigScopeType.USER,
                    scope_id=AppConfigScopeID(_USER_SCOPE_ID),
                ),
                config_names=["theme", "menu"],
            )
        )

        call_args = mock_session.request.call_args
        assert call_args[0][0] == "POST"
        assert str(call_args[0][1]).endswith("/v2/app-config-fragments/scoped/by-names")
        assert isinstance(result, AppConfigFragmentsByNamesPayload)
        assert [node.config_name if node is not None else None for node in result.root] == [
            "theme",
            None,
        ]


class TestScopedBulkUpsert:
    async def test_happy_path(
        self,
        client: V2AppConfigFragmentClient,
        mock_session: MagicMock,
        mock_response: AsyncMock,
        node_payload: dict[str, Any],
    ) -> None:
        mock_response.json = AsyncMock(
            return_value={"items": [node_payload]},
        )

        result = await client.scoped_bulk_upsert_app_config_fragments(
            ScopedUpsertAppConfigFragmentsInput(
                scope=AppConfigScopeRef(
                    scope_type=AppConfigScopeType.USER,
                    scope_id=AppConfigScopeID(_USER_SCOPE_ID),
                ),
                items=[AppConfigFragmentUpsertItem(config_name="theme", config={"mode": "dark"})],
            )
        )

        call_args = mock_session.request.call_args
        assert call_args[0][0] == "POST"
        assert str(call_args[0][1]).endswith("/v2/app-config-fragments/scoped/bulk-upsert")
        assert isinstance(result, UpsertAppConfigFragmentsPayload)
        assert [item.config_name for item in result.items] == ["theme"]


class TestScopedPurgeByNames:
    async def test_happy_path(
        self,
        client: V2AppConfigFragmentClient,
        mock_session: MagicMock,
        mock_response: AsyncMock,
        fragment_id: AppConfigFragmentID,
    ) -> None:
        mock_response.json = AsyncMock(return_value={"items": [str(fragment_id)]})

        result = await client.scoped_purge_app_config_fragments_by_names(
            ScopedPurgeAppConfigFragmentsByNamesInput(
                scope=AppConfigScopeRef(
                    scope_type=AppConfigScopeType.USER,
                    scope_id=AppConfigScopeID(_USER_SCOPE_ID),
                ),
                config_names=["theme"],
            )
        )

        call_args = mock_session.request.call_args
        assert call_args[0][0] == "POST"
        assert str(call_args[0][1]).endswith("/v2/app-config-fragments/scoped/by-names/bulk-delete")
        assert isinstance(result, PurgeAppConfigFragmentsByNamesPayload)
        assert result.items == [fragment_id]


class TestMyByNames:
    async def test_happy_path(
        self,
        client: V2AppConfigFragmentClient,
        mock_session: MagicMock,
        mock_response: AsyncMock,
        node_payload: dict[str, Any],
    ) -> None:
        mock_response.json = AsyncMock(return_value=[node_payload])

        result = await client.my_get_app_config_fragments_by_names(
            MyAppConfigFragmentsByNamesInput(config_names=["theme"])
        )

        call_args = mock_session.request.call_args
        assert call_args[0][0] == "POST"
        assert str(call_args[0][1]).endswith("/v2/app-config-fragments/my/by-names")
        assert isinstance(result, AppConfigFragmentsByNamesPayload)
        assert len(result.root) == 1


class TestMyBulkUpsert:
    async def test_happy_path(
        self,
        client: V2AppConfigFragmentClient,
        mock_session: MagicMock,
        mock_response: AsyncMock,
        node_payload: dict[str, Any],
    ) -> None:
        mock_response.json = AsyncMock(
            return_value={"items": [node_payload]},
        )

        result = await client.my_bulk_upsert_app_config_fragments(
            MyUpsertAppConfigFragmentsInput(
                items=[AppConfigFragmentUpsertItem(config_name="theme", config={"mode": "dark"})]
            )
        )

        call_args = mock_session.request.call_args
        assert call_args[0][0] == "POST"
        assert str(call_args[0][1]).endswith("/v2/app-config-fragments/my/bulk-upsert")
        assert isinstance(result, UpsertAppConfigFragmentsPayload)


class TestMyPurgeByNames:
    async def test_happy_path(
        self,
        client: V2AppConfigFragmentClient,
        mock_session: MagicMock,
        mock_response: AsyncMock,
        fragment_id: AppConfigFragmentID,
    ) -> None:
        mock_response.json = AsyncMock(return_value={"items": [str(fragment_id)]})

        result = await client.my_purge_app_config_fragments_by_names(
            MyPurgeAppConfigFragmentsByNamesInput(config_names=["theme"])
        )

        call_args = mock_session.request.call_args
        assert call_args[0][0] == "POST"
        assert str(call_args[0][1]).endswith("/v2/app-config-fragments/my/by-names/bulk-delete")
        assert isinstance(result, PurgeAppConfigFragmentsByNamesPayload)
        assert result.items == [fragment_id]


class TestGet:
    async def test_happy_path(
        self,
        client: V2AppConfigFragmentClient,
        mock_session: MagicMock,
        mock_response: AsyncMock,
        node_payload: dict[str, Any],
        fragment_id: AppConfigFragmentID,
    ) -> None:
        mock_response.json = AsyncMock(return_value=node_payload)

        result = await client.get(fragment_id)

        call_args = mock_session.request.call_args
        assert call_args[0][0] == "GET"
        assert str(call_args[0][1]).endswith(f"/v2/app-config-fragments/{fragment_id}")
        assert isinstance(result, AppConfigFragmentNode)
        assert result.config_name == "theme"


class TestPurge:
    async def test_happy_path(
        self,
        client: V2AppConfigFragmentClient,
        mock_session: MagicMock,
        mock_response: AsyncMock,
        fragment_id: AppConfigFragmentID,
    ) -> None:
        mock_response.json = AsyncMock(return_value={"id": str(fragment_id)})

        result = await client.purge(fragment_id)

        call_args = mock_session.request.call_args
        assert call_args[0][0] == "DELETE"
        assert str(call_args[0][1]).endswith(f"/v2/app-config-fragments/{fragment_id}")
        assert isinstance(result, PurgeAppConfigFragmentPayload)
        assert result.id == fragment_id


class TestBulkPurge:
    async def test_reports_each_item(
        self,
        client: V2AppConfigFragmentClient,
        mock_session: MagicMock,
        mock_response: AsyncMock,
        fragment_id: AppConfigFragmentID,
    ) -> None:
        missing_id = AppConfigFragmentID(uuid4())
        mock_response.json = AsyncMock(
            return_value={
                "items": [str(fragment_id)],
                "failed": [{"id": str(missing_id), "message": "not found"}],
            },
        )

        result = await client.bulk_purge(
            BulkPurgeAppConfigFragmentInput(ids=[fragment_id, missing_id])
        )

        call_args = mock_session.request.call_args
        assert call_args[0][0] == "POST"
        assert str(call_args[0][1]).endswith("/v2/app-config-fragments/bulk-delete")
        assert isinstance(result, BulkPurgeAppConfigFragmentPayload)
        assert result.items == [fragment_id]
        assert [item.id for item in result.failed] == [missing_id]


class TestAdminSearch:
    async def test_happy_path(
        self,
        client: V2AppConfigFragmentClient,
        mock_session: MagicMock,
        mock_response: AsyncMock,
        node_payload: dict[str, Any],
    ) -> None:
        mock_response.json = AsyncMock(
            return_value={
                "items": [{**node_payload, "config_name": "menu"}],
                "total_count": 1,
                "has_next_page": False,
                "has_previous_page": False,
            },
        )

        result = await client.admin_search(AdminSearchAppConfigFragmentInput(limit=10))

        call_args = mock_session.request.call_args
        assert call_args[0][0] == "POST"
        assert str(call_args[0][1]).endswith("/v2/app-config-fragments/admin/search")
        assert isinstance(result, SearchAppConfigFragmentPayload)
        assert [item.config_name for item in result.items] == ["menu"]
        assert result.total_count == 1
