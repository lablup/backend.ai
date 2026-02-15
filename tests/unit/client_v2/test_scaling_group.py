from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from yarl import URL

from ai.backend.client.v2.base_client import BackendAIClient
from ai.backend.client.v2.config import ClientConfig
from ai.backend.client.v2.domains.scaling_group import ScalingGroupClient
from ai.backend.common.dto.manager.scaling_group import (
    GetWsproxyVersionResponse,
    ListScalingGroupsResponse,
)

from .conftest import MockAuth

_DEFAULT_CONFIG = ClientConfig(endpoint=URL("https://api.example.com"))


def _make_request_session(resp: AsyncMock) -> MagicMock:
    mock_ctx = AsyncMock()
    mock_ctx.__aenter__ = AsyncMock(return_value=resp)
    mock_ctx.__aexit__ = AsyncMock(return_value=False)
    mock_session = MagicMock()
    mock_session.request = MagicMock(return_value=mock_ctx)
    return mock_session


def _make_client(mock_session: MagicMock) -> BackendAIClient:
    return BackendAIClient(_DEFAULT_CONFIG, MockAuth(), mock_session)


def _make_scaling_group_client(mock_session: MagicMock) -> ScalingGroupClient:
    return ScalingGroupClient(_make_client(mock_session))


class TestListScalingGroups:
    @pytest.mark.asyncio
    async def test_happy_path(self) -> None:
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(
            return_value={
                "scaling_groups": [
                    {"name": "default"},
                    {"name": "gpu-cluster"},
                ],
            }
        )
        mock_session = _make_request_session(mock_resp)
        client = _make_scaling_group_client(mock_session)

        result = await client.list_scaling_groups(group="my-group")

        call_args = mock_session.request.call_args
        assert call_args[0][0] == "GET"
        assert "/scaling-groups" in str(call_args[0][1])
        assert isinstance(result, ListScalingGroupsResponse)
        assert len(result.scaling_groups) == 2
        assert result.scaling_groups[0].name == "default"
        assert result.scaling_groups[1].name == "gpu-cluster"

    @pytest.mark.asyncio
    async def test_empty_list(self) -> None:
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(
            return_value={
                "scaling_groups": [],
            }
        )
        mock_session = _make_request_session(mock_resp)
        client = _make_scaling_group_client(mock_session)

        result = await client.list_scaling_groups(group="empty-group")

        assert isinstance(result, ListScalingGroupsResponse)
        assert len(result.scaling_groups) == 0

    @pytest.mark.asyncio
    async def test_group_param_passed(self) -> None:
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(
            return_value={
                "scaling_groups": [{"name": "default"}],
            }
        )
        mock_session = _make_request_session(mock_resp)
        client = _make_scaling_group_client(mock_session)

        await client.list_scaling_groups(group="test-group")

        call_kwargs = mock_session.request.call_args.kwargs
        assert call_kwargs["params"]["group"] == "test-group"


class TestGetWsproxyVersion:
    @pytest.mark.asyncio
    async def test_happy_path(self) -> None:
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(
            return_value={
                "wsproxy_version": "v5.20240101",
            }
        )
        mock_session = _make_request_session(mock_resp)
        client = _make_scaling_group_client(mock_session)

        result = await client.get_wsproxy_version("default")

        call_args = mock_session.request.call_args
        assert call_args[0][0] == "GET"
        assert "/scaling-groups/default/wsproxy-version" in str(call_args[0][1])
        assert isinstance(result, GetWsproxyVersionResponse)
        assert result.wsproxy_version == "v5.20240101"

    @pytest.mark.asyncio
    async def test_scaling_group_name_in_path(self) -> None:
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(
            return_value={
                "wsproxy_version": "v4.20231201",
            }
        )
        mock_session = _make_request_session(mock_resp)
        client = _make_scaling_group_client(mock_session)

        result = await client.get_wsproxy_version("gpu-cluster")

        call_args = mock_session.request.call_args
        assert "/scaling-groups/gpu-cluster/wsproxy-version" in str(call_args[0][1])
        assert isinstance(result, GetWsproxyVersionResponse)
        assert result.wsproxy_version == "v4.20231201"
