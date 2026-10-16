from __future__ import annotations

from uuid import UUID

from ai.backend.client.v2.base_domain import BaseDomainClient
from ai.backend.common.dto.manager.v2.common import PartialBulkPayload
from ai.backend.common.dto.manager.v2.deployment_revision_preset.request import (
    CreateDeploymentRevisionPresetInput,
    PartialBulkPurgeDeploymentRevisionPresetsInput,
    PartialBulkUpdateDeploymentRevisionPresetsInput,
    SearchDeploymentRevisionPresetsInput,
    UpdateDeploymentRevisionPresetInput,
)
from ai.backend.common.dto.manager.v2.deployment_revision_preset.response import (
    CreateDeploymentRevisionPresetPayload,
    DeleteDeploymentRevisionPresetPayload,
    DeploymentRevisionPresetNode,
    SearchDeploymentRevisionPresetsPayload,
    UpdateDeploymentRevisionPresetPayload,
)

_PATH = "/v2/deployments/revision-presets"


class V2DeploymentRevisionPresetClient(BaseDomainClient):
    async def search(
        self, request: SearchDeploymentRevisionPresetsInput
    ) -> SearchDeploymentRevisionPresetsPayload:
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/search",
            request=request,
            response_model=SearchDeploymentRevisionPresetsPayload,
        )

    async def get(self, preset_id: UUID) -> DeploymentRevisionPresetNode:
        return await self._client.typed_request(
            "GET",
            f"{_PATH}/{preset_id}",
            response_model=DeploymentRevisionPresetNode,
        )

    async def create(
        self, request: CreateDeploymentRevisionPresetInput
    ) -> CreateDeploymentRevisionPresetPayload:
        return await self._client.typed_request(
            "POST",
            _PATH,
            request=request,
            response_model=CreateDeploymentRevisionPresetPayload,
        )

    async def update(
        self, preset_id: UUID, request: UpdateDeploymentRevisionPresetInput
    ) -> UpdateDeploymentRevisionPresetPayload:
        return await self._client.typed_request(
            "PATCH",
            f"{_PATH}/{preset_id}",
            request=request,
            response_model=UpdateDeploymentRevisionPresetPayload,
        )

    async def purge(self, preset_id: UUID) -> DeleteDeploymentRevisionPresetPayload:
        """Permanently remove a preset."""
        return await self._client.typed_request(
            "DELETE",
            f"{_PATH}/{preset_id}",
            response_model=DeleteDeploymentRevisionPresetPayload,
        )

    async def delete(self, preset_id: UUID) -> DeleteDeploymentRevisionPresetPayload:
        """Deprecated. Use :meth:`purge`."""
        return await self.purge(preset_id)

    async def partial_bulk_update(
        self, request: PartialBulkUpdateDeploymentRevisionPresetsInput
    ) -> PartialBulkPayload[DeploymentRevisionPresetNode]:
        """Update several presets, answering for each one."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/partial-bulk-update",
            request=request,
            response_model=PartialBulkPayload[DeploymentRevisionPresetNode],
        )

    async def partial_bulk_purge(
        self, request: PartialBulkPurgeDeploymentRevisionPresetsInput
    ) -> PartialBulkPayload[DeploymentRevisionPresetNode]:
        """Permanently remove several presets, answering for each one."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/partial-bulk-purge",
            request=request,
            response_model=PartialBulkPayload[DeploymentRevisionPresetNode],
        )
