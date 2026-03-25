from __future__ import annotations

from ai.backend.client.v2.base_domain import BaseDomainClient
from ai.backend.common.dto.manager.scaling_group import (
    GetWsproxyVersionResponse,
    ListScalingGroupsResponse,
)

API_PREFIX = "/scaling-groups"


class ScalingGroupClient(BaseDomainClient):
    """Client for scaling group endpoints."""

    async def list_scaling_groups(
        self,
        group: str,
    ) -> ListScalingGroupsResponse:
        return await self._client.typed_request(
            "GET",
            API_PREFIX,
            params={"group": group},
            response_model=ListScalingGroupsResponse,
        )

    async def get_wsproxy_version(
        self,
        scaling_group: str,
    ) -> GetWsproxyVersionResponse:
        return await self._client.typed_request(
            "GET",
            f"{API_PREFIX}/{scaling_group}/wsproxy-version",
            response_model=GetWsproxyVersionResponse,
        )
