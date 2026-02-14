from unittest.mock import AsyncMock, MagicMock

import pytest
from yarl import URL

from ai.backend.client.v2.base_client import BackendAIClient
from ai.backend.client.v2.config import ClientConfig
from ai.backend.client.v2.domains.infra import InfraClient
from ai.backend.common.dto.manager.infra import (
    CheckPresetsRequest,
    CheckPresetsResponse,
    DeleteConfigRequest,
    DeleteConfigResponse,
    GetConfigRequest,
    GetConfigResponse,
    GetContainerRegistriesResponse,
    GetResourceMetadataRequest,
    GetResourceMetadataResponse,
    GetResourceSlotsResponse,
    GetVFolderTypesResponse,
    GetWSProxyVersionRequest,
    GetWSProxyVersionResponse,
    ListPresetsRequest,
    ListPresetsResponse,
    ListScalingGroupsRequest,
    ListScalingGroupsResponse,
    MonthStatsResponse,
    RecalculateUsageResponse,
    SetConfigRequest,
    SetConfigResponse,
    UsagePerMonthRequest,
    UsagePerMonthResponse,
    UsagePerPeriodRequest,
    UsagePerPeriodResponse,
    WatcherAgentActionResponse,
    WatcherAgentRequest,
    WatcherStatusResponse,
)

from .conftest import MockAuth

_DEFAULT_CONFIG = ClientConfig(endpoint=URL("https://api.example.com"))


def _make_client(mock_session: MagicMock | None = None) -> BackendAIClient:
    return BackendAIClient(
        _DEFAULT_CONFIG,
        MockAuth(),
        mock_session or MagicMock(),
    )


def _make_request_session(resp: AsyncMock) -> MagicMock:
    mock_ctx = AsyncMock()
    mock_ctx.__aenter__ = AsyncMock(return_value=resp)
    mock_ctx.__aexit__ = AsyncMock(return_value=False)
    mock_session = MagicMock()
    mock_session.request = MagicMock(return_value=mock_ctx)
    return mock_session


def _ok_response(data: dict[str, object] | list[object]) -> AsyncMock:
    resp = AsyncMock()
    resp.status = 200
    resp.json = AsyncMock(return_value=data)
    return resp


class TestInfraClientEtcdConfig:
    @pytest.mark.asyncio
    async def test_get_resource_slots(self) -> None:
        mock_resp = _ok_response({"cpu": "count", "mem": "bytes", "cuda.device": "count"})
        mock_session = _make_request_session(mock_resp)
        client = _make_client(mock_session)
        infra = InfraClient(client)

        result = await infra.get_resource_slots()

        assert isinstance(result, GetResourceSlotsResponse)
        assert result.root == {"cpu": "count", "mem": "bytes", "cuda.device": "count"}
        call_args = mock_session.request.call_args
        assert call_args[0][0] == "GET"
        assert "/config/resource-slots" in str(call_args[0][1])

    @pytest.mark.asyncio
    async def test_get_resource_metadata(self) -> None:
        mock_resp = _ok_response({
            "cpu": {
                "slot_name": "cpu",
                "description": "CPU core",
                "human_readable_name": "CPU",
                "display_unit": "Core",
                "number_format": {"binary": False, "round_length": 2},
                "display_icon": "cpu-icon",
            }
        })
        mock_session = _make_request_session(mock_resp)
        client = _make_client(mock_session)
        infra = InfraClient(client)

        request = GetResourceMetadataRequest(sgroup="default")
        result = await infra.get_resource_metadata(request)

        assert isinstance(result, GetResourceMetadataResponse)
        assert "cpu" in result.root
        assert result.root["cpu"].slot_name == "cpu"
        call_args = mock_session.request.call_args
        assert call_args.kwargs["params"] == {"sgroup": "default"}

    @pytest.mark.asyncio
    async def test_get_resource_metadata_no_filter(self) -> None:
        mock_resp = _ok_response({
            "cpu": {
                "slot_name": "cpu",
                "description": "CPU",
                "human_readable_name": "CPU",
                "display_unit": "Core",
                "number_format": {"binary": False, "round_length": 2},
                "display_icon": "cpu-icon",
            }
        })
        mock_session = _make_request_session(mock_resp)
        client = _make_client(mock_session)
        infra = InfraClient(client)

        result = await infra.get_resource_metadata()

        assert isinstance(result, GetResourceMetadataResponse)
        call_args = mock_session.request.call_args
        assert call_args.kwargs["params"] is None

    @pytest.mark.asyncio
    async def test_get_vfolder_types(self) -> None:
        mock_resp = _ok_response(["user", "group"])
        mock_session = _make_request_session(mock_resp)
        client = _make_client(mock_session)
        infra = InfraClient(client)

        result = await infra.get_vfolder_types()

        assert isinstance(result, GetVFolderTypesResponse)
        assert result.root == ["user", "group"]

    @pytest.mark.asyncio
    async def test_get_config(self) -> None:
        mock_resp = _ok_response({"result": "some_value"})
        mock_session = _make_request_session(mock_resp)
        client = _make_client(mock_session)
        infra = InfraClient(client)

        request = GetConfigRequest(key="config/docker/registry")
        result = await infra.get_config(request)

        assert isinstance(result, GetConfigResponse)
        assert result.result == "some_value"
        call_args = mock_session.request.call_args
        assert call_args[0][0] == "POST"
        assert "/config/get" in str(call_args[0][1])

    @pytest.mark.asyncio
    async def test_set_config(self) -> None:
        mock_resp = _ok_response({"result": "ok"})
        mock_session = _make_request_session(mock_resp)
        client = _make_client(mock_session)
        infra = InfraClient(client)

        request = SetConfigRequest(key="config/docker/registry", value="cr.example.com")
        result = await infra.set_config(request)

        assert isinstance(result, SetConfigResponse)
        assert result.result == "ok"

    @pytest.mark.asyncio
    async def test_delete_config(self) -> None:
        mock_resp = _ok_response({"result": "ok"})
        mock_session = _make_request_session(mock_resp)
        client = _make_client(mock_session)
        infra = InfraClient(client)

        request = DeleteConfigRequest(key="config/docker/registry")
        result = await infra.delete_config(request)

        assert isinstance(result, DeleteConfigResponse)
        assert result.result == "ok"
        call_args = mock_session.request.call_args
        assert call_args[0][0] == "POST"

    @pytest.mark.asyncio
    async def test_get_container_registries(self) -> None:
        mock_resp = _ok_response({"cr.example.com": {"username": "user", "project": ["proj"]}})
        mock_session = _make_request_session(mock_resp)
        client = _make_client(mock_session)
        infra = InfraClient(client)

        result = await infra.get_container_registries()

        assert isinstance(result, GetContainerRegistriesResponse)
        assert "cr.example.com" in result.root


class TestInfraClientScalingGroups:
    @pytest.mark.asyncio
    async def test_list_scaling_groups(self) -> None:
        mock_resp = _ok_response({"scaling_groups": [{"name": "default"}, {"name": "gpu-cluster"}]})
        mock_session = _make_request_session(mock_resp)
        client = _make_client(mock_session)
        infra = InfraClient(client)

        request = ListScalingGroupsRequest(group="my-group")
        result = await infra.list_scaling_groups(request)

        assert isinstance(result, ListScalingGroupsResponse)
        assert len(result.scaling_groups) == 2
        assert result.scaling_groups[0].name == "default"

    @pytest.mark.asyncio
    async def test_get_wsproxy_version(self) -> None:
        mock_resp = _ok_response({"wsproxy_version": 2})
        mock_session = _make_request_session(mock_resp)
        client = _make_client(mock_session)
        infra = InfraClient(client)

        result = await infra.get_wsproxy_version("default")

        assert isinstance(result, GetWSProxyVersionResponse)
        assert result.wsproxy_version == 2
        call_args = mock_session.request.call_args
        assert "/scaling-groups/default/wsproxy-version" in str(call_args[0][1])

    @pytest.mark.asyncio
    async def test_get_wsproxy_version_with_request(self) -> None:
        mock_resp = _ok_response({"wsproxy_version": 3})
        mock_session = _make_request_session(mock_resp)
        client = _make_client(mock_session)
        infra = InfraClient(client)

        request = GetWSProxyVersionRequest(group="my-group")
        result = await infra.get_wsproxy_version("gpu-cluster", request)

        assert isinstance(result, GetWSProxyVersionResponse)
        assert result.wsproxy_version == 3
        call_args = mock_session.request.call_args
        assert "/scaling-groups/gpu-cluster/wsproxy-version" in str(call_args[0][1])


class TestInfraClientResources:
    @pytest.mark.asyncio
    async def test_list_presets(self) -> None:
        mock_resp = _ok_response({
            "presets": [{"name": "small", "resource_slots": {"cpu": "1", "mem": "1g"}}]
        })
        mock_session = _make_request_session(mock_resp)
        client = _make_client(mock_session)
        infra = InfraClient(client)

        result = await infra.list_presets()

        assert isinstance(result, ListPresetsResponse)
        assert len(result.presets) == 1

    @pytest.mark.asyncio
    async def test_list_presets_with_scaling_group(self) -> None:
        mock_resp = _ok_response({"presets": []})
        mock_session = _make_request_session(mock_resp)
        client = _make_client(mock_session)
        infra = InfraClient(client)

        request = ListPresetsRequest(scaling_group="default")
        result = await infra.list_presets(request)

        assert isinstance(result, ListPresetsResponse)
        call_args = mock_session.request.call_args
        assert call_args.kwargs["params"] == {"scaling_group": "default"}

    @pytest.mark.asyncio
    async def test_check_presets(self) -> None:
        mock_resp = _ok_response({
            "presets": [],
            "keypair_limits": {},
            "keypair_using": {},
            "keypair_remaining": {},
            "group_limits": {},
            "group_using": {},
            "group_remaining": {},
            "scaling_group_remaining": {},
            "scaling_groups": {},
        })
        mock_session = _make_request_session(mock_resp)
        client = _make_client(mock_session)
        infra = InfraClient(client)

        request = CheckPresetsRequest(scaling_group="default", group="my-group")
        result = await infra.check_presets(request)

        assert isinstance(result, CheckPresetsResponse)
        call_args = mock_session.request.call_args
        assert call_args[0][0] == "POST"

    @pytest.mark.asyncio
    async def test_recalculate_usage(self) -> None:
        mock_resp = _ok_response({})
        mock_session = _make_request_session(mock_resp)
        client = _make_client(mock_session)
        infra = InfraClient(client)

        result = await infra.recalculate_usage()

        assert isinstance(result, RecalculateUsageResponse)
        call_args = mock_session.request.call_args
        assert call_args[0][0] == "POST"
        assert "/resource/recalculate-usage" in str(call_args[0][1])


class TestInfraClientUsageStats:
    @pytest.mark.asyncio
    async def test_get_usage_per_month(self) -> None:
        mock_resp = _ok_response([{"session_id": "abc", "cpu": 2}])
        mock_session = _make_request_session(mock_resp)
        client = _make_client(mock_session)
        infra = InfraClient(client)

        request = UsagePerMonthRequest(group_ids=None, month="202506")
        result = await infra.get_usage_per_month(request)

        assert isinstance(result, UsagePerMonthResponse)
        assert len(result.root) == 1
        call_args = mock_session.request.call_args
        assert call_args[0][0] == "GET"
        assert call_args.kwargs["json"]["month"] == "202506"

    @pytest.mark.asyncio
    async def test_get_usage_per_period(self) -> None:
        mock_resp = _ok_response([{"session_id": "def", "cpu": 4}])
        mock_session = _make_request_session(mock_resp)
        client = _make_client(mock_session)
        infra = InfraClient(client)

        request = UsagePerPeriodRequest(start_date="20250601", end_date="20250630")
        result = await infra.get_usage_per_period(request)

        assert isinstance(result, UsagePerPeriodResponse)
        assert len(result.root) == 1

    @pytest.mark.asyncio
    async def test_get_user_month_stats(self) -> None:
        mock_resp = _ok_response([{"count": 10, "timestamp": "2025-06-01"}])
        mock_session = _make_request_session(mock_resp)
        client = _make_client(mock_session)
        infra = InfraClient(client)

        result = await infra.get_user_month_stats()

        assert isinstance(result, MonthStatsResponse)
        assert len(result.root) == 1
        call_args = mock_session.request.call_args
        assert "/resource/stats/user/month" in str(call_args[0][1])

    @pytest.mark.asyncio
    async def test_get_admin_month_stats(self) -> None:
        mock_resp = _ok_response([{"count": 100, "timestamp": "2025-06-01"}])
        mock_session = _make_request_session(mock_resp)
        client = _make_client(mock_session)
        infra = InfraClient(client)

        result = await infra.get_admin_month_stats()

        assert isinstance(result, MonthStatsResponse)
        call_args = mock_session.request.call_args
        assert "/resource/stats/admin/month" in str(call_args[0][1])


class TestInfraClientWatcher:
    @pytest.mark.asyncio
    async def test_get_watcher_status(self) -> None:
        mock_resp = _ok_response({"status": "running", "version": "1.0"})
        mock_session = _make_request_session(mock_resp)
        client = _make_client(mock_session)
        infra = InfraClient(client)

        request = WatcherAgentRequest(agent_id="agent-001")
        result = await infra.get_watcher_status(request)

        assert isinstance(result, WatcherStatusResponse)
        assert result.root["status"] == "running"
        call_args = mock_session.request.call_args
        assert call_args[0][0] == "GET"
        assert call_args.kwargs["json"]["agent_id"] == "agent-001"

    @pytest.mark.asyncio
    async def test_start_watcher_agent(self) -> None:
        mock_resp = _ok_response({"status": "started"})
        mock_session = _make_request_session(mock_resp)
        client = _make_client(mock_session)
        infra = InfraClient(client)

        request = WatcherAgentRequest(agent_id="agent-001")
        result = await infra.start_watcher_agent(request)

        assert isinstance(result, WatcherAgentActionResponse)
        assert result.root["status"] == "started"
        call_args = mock_session.request.call_args
        assert call_args[0][0] == "POST"
        assert "/resource/watcher/agent/start" in str(call_args[0][1])

    @pytest.mark.asyncio
    async def test_stop_watcher_agent(self) -> None:
        mock_resp = _ok_response({"status": "stopped"})
        mock_session = _make_request_session(mock_resp)
        client = _make_client(mock_session)
        infra = InfraClient(client)

        request = WatcherAgentRequest(agent_id="agent-001")
        result = await infra.stop_watcher_agent(request)

        assert isinstance(result, WatcherAgentActionResponse)
        assert result.root["status"] == "stopped"
        call_args = mock_session.request.call_args
        assert "/resource/watcher/agent/stop" in str(call_args[0][1])

    @pytest.mark.asyncio
    async def test_restart_watcher_agent(self) -> None:
        mock_resp = _ok_response({"status": "restarted"})
        mock_session = _make_request_session(mock_resp)
        client = _make_client(mock_session)
        infra = InfraClient(client)

        request = WatcherAgentRequest(agent_id="agent-001")
        result = await infra.restart_watcher_agent(request)

        assert isinstance(result, WatcherAgentActionResponse)
        assert result.root["status"] == "restarted"
        call_args = mock_session.request.call_args
        assert "/resource/watcher/agent/restart" in str(call_args[0][1])
