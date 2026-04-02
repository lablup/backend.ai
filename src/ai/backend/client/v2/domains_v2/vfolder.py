"""V2 REST SDK client for the VFolder resource."""

from __future__ import annotations

from uuid import UUID

from ai.backend.client.v2.base_domain import BaseDomainClient
from ai.backend.common.dto.manager.v2.vfolder.request import SearchVFoldersInput
from ai.backend.common.dto.manager.v2.vfolder.response import SearchVFoldersPayload

_PATH = "/v2/vfolders"


class V2VFolderClient(BaseDomainClient):
    """SDK client for ``/v2/vfolders`` endpoints."""

    async def project_search(
        self,
        project_id: UUID,
        request: SearchVFoldersInput,
    ) -> SearchVFoldersPayload:
        """Search vfolders within a project."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/projects/{project_id}/search",
            request=request,
            response_model=SearchVFoldersPayload,
        )
