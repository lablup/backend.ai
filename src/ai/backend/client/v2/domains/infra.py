from __future__ import annotations

from ai.backend.client.v2.base_domain import BaseDomainClient
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


class InfraClient(BaseDomainClient):
    """SDK v2 client for infrastructure endpoints.

    Covers etcd config, scaling groups, resource presets, usage stats,
    and watcher agent operations.
    """

    # ---- Etcd Config ----

    async def get_resource_slots(self) -> GetResourceSlotsResponse:
        data = await self._client._request("GET", "/config/resource-slots")
        return GetResourceSlotsResponse.model_validate(data)

    async def get_resource_metadata(
        self, request: GetResourceMetadataRequest | None = None
    ) -> GetResourceMetadataResponse:
        params = None
        if request is not None and request.sgroup is not None:
            params = {"sgroup": request.sgroup}
        data = await self._client._request("GET", "/config/resource-slots/details", params=params)
        return GetResourceMetadataResponse.model_validate(data)

    async def get_vfolder_types(self) -> GetVFolderTypesResponse:
        data = await self._client._request("GET", "/config/vfolder-types")
        return GetVFolderTypesResponse.model_validate(data)

    async def get_config(self, request: GetConfigRequest) -> GetConfigResponse:
        return await self._client.typed_request(
            "POST",
            "/config/get",
            request=request,
            response_model=GetConfigResponse,
        )

    async def set_config(self, request: SetConfigRequest) -> SetConfigResponse:
        return await self._client.typed_request(
            "POST",
            "/config/set",
            request=request,
            response_model=SetConfigResponse,
        )

    async def delete_config(self, request: DeleteConfigRequest) -> DeleteConfigResponse:
        return await self._client.typed_request(
            "POST",
            "/config/delete",
            request=request,
            response_model=DeleteConfigResponse,
        )

    async def get_container_registries(self) -> GetContainerRegistriesResponse:
        data = await self._client._request("GET", "/config/docker-registries")
        return GetContainerRegistriesResponse.model_validate(data)

    # ---- Scaling Groups ----

    async def list_scaling_groups(
        self, request: ListScalingGroupsRequest
    ) -> ListScalingGroupsResponse:
        return await self._client.typed_request(
            "GET",
            "/scaling-groups",
            request=request,
            response_model=ListScalingGroupsResponse,
        )

    async def get_wsproxy_version(
        self, scaling_group: str, request: GetWSProxyVersionRequest | None = None
    ) -> GetWSProxyVersionResponse:
        return await self._client.typed_request(
            "GET",
            f"/scaling-groups/{scaling_group}/wsproxy-version",
            request=request,
            response_model=GetWSProxyVersionResponse,
        )

    # ---- Resources ----

    async def list_presets(self, request: ListPresetsRequest | None = None) -> ListPresetsResponse:
        params = None
        if request is not None and request.scaling_group is not None:
            params = {"scaling_group": request.scaling_group}
        return await self._client.typed_request(
            "GET",
            "/resource/presets",
            response_model=ListPresetsResponse,
            params=params,
        )

    async def check_presets(self, request: CheckPresetsRequest) -> CheckPresetsResponse:
        return await self._client.typed_request(
            "POST",
            "/resource/check-presets",
            request=request,
            response_model=CheckPresetsResponse,
        )

    async def recalculate_usage(self) -> RecalculateUsageResponse:
        return await self._client.typed_request(
            "POST",
            "/resource/recalculate-usage",
            response_model=RecalculateUsageResponse,
        )

    async def get_usage_per_month(self, request: UsagePerMonthRequest) -> UsagePerMonthResponse:
        json_body = request.model_dump(exclude_none=True)
        data = await self._client._request("GET", "/resource/usage/month", json=json_body)
        return UsagePerMonthResponse.model_validate(data)

    async def get_usage_per_period(self, request: UsagePerPeriodRequest) -> UsagePerPeriodResponse:
        json_body = request.model_dump(exclude_none=True)
        data = await self._client._request("GET", "/resource/usage/period", json=json_body)
        return UsagePerPeriodResponse.model_validate(data)

    async def get_user_month_stats(self) -> MonthStatsResponse:
        data = await self._client._request("GET", "/resource/stats/user/month")
        return MonthStatsResponse.model_validate(data)

    async def get_admin_month_stats(self) -> MonthStatsResponse:
        data = await self._client._request("GET", "/resource/stats/admin/month")
        return MonthStatsResponse.model_validate(data)

    # ---- Watcher ----

    async def get_watcher_status(self, request: WatcherAgentRequest) -> WatcherStatusResponse:
        json_body = request.model_dump(exclude_none=True)
        data = await self._client._request("GET", "/resource/watcher", json=json_body)
        return WatcherStatusResponse.model_validate(data)

    async def start_watcher_agent(self, request: WatcherAgentRequest) -> WatcherAgentActionResponse:
        json_body = request.model_dump(exclude_none=True)
        data = await self._client._request("POST", "/resource/watcher/agent/start", json=json_body)
        return WatcherAgentActionResponse.model_validate(data)

    async def stop_watcher_agent(self, request: WatcherAgentRequest) -> WatcherAgentActionResponse:
        json_body = request.model_dump(exclude_none=True)
        data = await self._client._request("POST", "/resource/watcher/agent/stop", json=json_body)
        return WatcherAgentActionResponse.model_validate(data)

    async def restart_watcher_agent(
        self, request: WatcherAgentRequest
    ) -> WatcherAgentActionResponse:
        json_body = request.model_dump(exclude_none=True)
        data = await self._client._request(
            "POST", "/resource/watcher/agent/restart", json=json_body
        )
        return WatcherAgentActionResponse.model_validate(data)
