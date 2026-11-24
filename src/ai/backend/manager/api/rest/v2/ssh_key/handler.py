"""REST v2 handler for the SSH key domain."""

from __future__ import annotations

from http import HTTPStatus
from typing import TYPE_CHECKING

from ai.backend.common.api_handlers import APIResponse, BodyParam, PathParam
from ai.backend.common.dto.manager.v2.ssh_key.request import (
    MySearchSSHKeysInput,
    MyUploadSSHKeyInput,
    ScopedSearchSSHKeysInput,
)
from ai.backend.manager.api.rest.v2.path_params import SSHKeyIdPathParam
from ai.backend.manager.dto.context import UserContext

if TYPE_CHECKING:
    from ai.backend.manager.api.adapters.ssh_key.adapter import SSHKeyAdapter


class V2SSHKeyHandler:
    """REST v2 handler for uploading, reading and searching SSH keys and switching the default."""

    def __init__(self, *, adapter: SSHKeyAdapter) -> None:
        self._adapter = adapter

    async def my_upload(
        self,
        body: BodyParam[MyUploadSSHKeyInput],
    ) -> APIResponse:
        """Upload a public key to the current user."""
        result = await self._adapter.my_upload(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.CREATED, response_model=result)

    async def switch_default(
        self,
        path: PathParam[SSHKeyIdPathParam],
    ) -> APIResponse:
        """Make an SSH key the default of its owner."""
        result = await self._adapter.switch_default(path.parsed.ssh_key_id)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def get(self, path: PathParam[SSHKeyIdPathParam]) -> APIResponse:
        """Read one SSH key."""
        result = await self._adapter.get(path.parsed.ssh_key_id)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def my_search(
        self, user_ctx: UserContext, body: BodyParam[MySearchSSHKeysInput]
    ) -> APIResponse:
        """Search the current user's own SSH keys."""
        result = await self._adapter.scoped_search(
            ScopedSearchSSHKeysInput(
                user_id=user_ctx.user_uuid,
                filter=body.parsed.filter,
                order=body.parsed.order,
                first=body.parsed.first,
                after=body.parsed.after,
                last=body.parsed.last,
                before=body.parsed.before,
                limit=body.parsed.limit,
                offset=body.parsed.offset,
            )
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)
