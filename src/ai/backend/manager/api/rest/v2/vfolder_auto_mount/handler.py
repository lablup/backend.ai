"""REST v2 handler for the vfolder auto-mount domain."""

from __future__ import annotations

from http import HTTPStatus
from typing import TYPE_CHECKING

from ai.backend.common.api_handlers import APIResponse, BodyParam, PathParam
from ai.backend.common.dto.manager.v2.vfolder_auto_mount.request import (
    CreateVFolderAutoMountInput,
    DeleteVFolderAutoMountInput,
    ScopedSearchVFolderAutoMountsInput,
    UpdateVFolderAutoMountInput,
)
from ai.backend.manager.api.rest.v2.path_params import VFolderAutoMountIdPathParam

if TYPE_CHECKING:
    from ai.backend.manager.api.adapters.vfolder_auto_mount.adapter import (
        VFolderAutoMountAdapter,
    )


class V2VFolderAutoMountHandler:
    """REST v2 handler for adding, updating, deleting and reading vfolder auto-mounts."""

    def __init__(self, *, adapter: VFolderAutoMountAdapter) -> None:
        self._adapter = adapter

    async def create(
        self,
        body: BodyParam[CreateVFolderAutoMountInput],
    ) -> APIResponse:
        """Auto-mount a vfolder of a project into every session created in it."""
        result = await self._adapter.create(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.CREATED, response_model=result)

    async def scoped_search(
        self,
        body: BodyParam[ScopedSearchVFolderAutoMountsInput],
    ) -> APIResponse:
        """Search the auto-mounts of the named projects, combined with OR."""
        result = await self._adapter.scoped_search(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def update(
        self,
        path: PathParam[VFolderAutoMountIdPathParam],
        body: BodyParam[UpdateVFolderAutoMountInput],
    ) -> APIResponse:
        """Change an auto-mount's destination, subpath or permission."""
        input_ = body.parsed.model_copy(update={"id": path.parsed.vfolder_auto_mount_id})
        result = await self._adapter.update(input_)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def delete(
        self,
        path: PathParam[VFolderAutoMountIdPathParam],
    ) -> APIResponse:
        """Mark an auto-mount deleted."""
        result = await self._adapter.delete(
            DeleteVFolderAutoMountInput(id=path.parsed.vfolder_auto_mount_id)
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)
