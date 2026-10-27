"""V2 SDK client for the system session environ domain."""

from __future__ import annotations

from ai.backend.client.v2.base_domain import BaseDomainClient
from ai.backend.common.data.entity.system_session_environ import SystemSessionEnvironID
from ai.backend.common.dto.manager.v2.system_session_environ.request import (
    AdminSearchSystemSessionEnvironsInput,
    UpdateSystemSessionEnvironInput,
)
from ai.backend.common.dto.manager.v2.system_session_environ.response import (
    AdminSearchSystemSessionEnvironsPayload,
    DeleteSystemSessionEnvironPayload,
    ListSystemSessionEnvironValueSourcesPayload,
    RestoreSystemSessionEnvironPayload,
    UpdateSystemSessionEnvironPayload,
)

_PATH = "/v2/system-session-environs"


class V2SystemSessionEnvironClient(BaseDomainClient):
    """SDK client for the system session environ domain."""

    async def admin_search(
        self, request: AdminSearchSystemSessionEnvironsInput
    ) -> AdminSearchSystemSessionEnvironsPayload:
        """Search every system session environ row, at every scope (superadmin only)."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/search",
            request=request,
            response_model=AdminSearchSystemSessionEnvironsPayload,
        )

    async def list_value_sources(self) -> ListSystemSessionEnvironValueSourcesPayload:
        """List every value source a system session environ row can carry."""
        return await self._client.typed_request(
            "GET",
            f"{_PATH}/value-sources",
            response_model=ListSystemSessionEnvironValueSourcesPayload,
        )

    async def update(
        self, request: UpdateSystemSessionEnvironInput
    ) -> UpdateSystemSessionEnvironPayload:
        """Change a system session environ row's key."""
        return await self._client.typed_request(
            "PATCH",
            f"{_PATH}/{request.id}",
            request=request,
            response_model=UpdateSystemSessionEnvironPayload,
        )

    async def delete(self, environ_id: SystemSessionEnvironID) -> DeleteSystemSessionEnvironPayload:
        """Soft-delete a system session environ row."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/{environ_id}/delete",
            response_model=DeleteSystemSessionEnvironPayload,
        )

    async def restore(
        self, environ_id: SystemSessionEnvironID
    ) -> RestoreSystemSessionEnvironPayload:
        """Restore a soft-deleted system session environ row."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/{environ_id}/restore",
            response_model=RestoreSystemSessionEnvironPayload,
        )
