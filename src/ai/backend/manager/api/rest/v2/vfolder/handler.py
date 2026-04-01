"""REST v2 handlers for the VFolder domain."""

from __future__ import annotations

from http import HTTPStatus
from typing import TYPE_CHECKING

from ai.backend.common.api_handlers import APIResponse, BodyParam, PathParam
from ai.backend.common.dto.manager.v2.vfolder.request import SearchVFoldersInput
from ai.backend.manager.api.rest.v2.path_params import ProjectIdPathParam

if TYPE_CHECKING:
    from ai.backend.manager.api.adapters.vfolder import VFolderAdapter


class V2VFolderHandler:
    """REST v2 handler for VFolder endpoints."""

    def __init__(self, *, adapter: VFolderAdapter) -> None:
        self._adapter = adapter

    async def project_search(
        self,
        path: PathParam[ProjectIdPathParam],
        body: BodyParam[SearchVFoldersInput],
    ) -> APIResponse:
        """Search vfolders within a project."""
        result = await self._adapter.project_search(path.parsed.project_id, body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)
