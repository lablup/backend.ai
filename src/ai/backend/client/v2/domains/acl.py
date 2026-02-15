from __future__ import annotations

from ai.backend.client.v2.base_domain import BaseDomainClient
from ai.backend.common.dto.manager.acl import (
    GetPermissionsResponse,
)


class ACLClient(BaseDomainClient):
    API_PREFIX = "/acl"

    async def get_permissions(self) -> GetPermissionsResponse:
        return await self._client.typed_request(
            "GET",
            self.API_PREFIX,
            response_model=GetPermissionsResponse,
        )
