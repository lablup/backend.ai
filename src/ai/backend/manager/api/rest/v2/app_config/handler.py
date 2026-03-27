"""REST v2 handler for the app configuration domain."""

from __future__ import annotations

import logging
from http import HTTPStatus
from typing import TYPE_CHECKING, Final

from aiohttp import web

from ai.backend.common.api_handlers import APIResponse, BodyParam, PathParam
from ai.backend.common.dto.manager.v2.app_config.request import (
    UpsertDomainConfigInput,
    UpsertUserConfigInput,
)
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.api.rest.v2.path_params import DomainNamePathParam, UserIdPathParam

if TYPE_CHECKING:
    from ai.backend.manager.api.adapters.app_config import AppConfigAdapter

log: Final = BraceStyleAdapter(logging.getLogger(__spec__.name))


class V2AppConfigHandler:
    """REST v2 handler for app configuration operations."""

    def __init__(self, *, adapter: AppConfigAdapter) -> None:
        self._adapter = adapter

    # ------------------------------------------------------------------ domain config

    async def get_domain_config(
        self,
        path: PathParam[DomainNamePathParam],
    ) -> APIResponse:
        """Get domain-level app configuration."""
        result = await self._adapter.get_domain_config(path.parsed.domain_name)
        if result is None:
            raise web.HTTPNotFound(reason="Domain config not found")
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def upsert_domain_config(
        self,
        path: PathParam[DomainNamePathParam],
        body: BodyParam[UpsertDomainConfigInput],
    ) -> APIResponse:
        """Create or update domain-level app configuration."""
        result = await self._adapter.upsert_domain_config(
            path.parsed.domain_name, body.parsed.extra_config
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def delete_domain_config(
        self,
        path: PathParam[DomainNamePathParam],
    ) -> APIResponse:
        """Delete domain-level app configuration."""
        result = await self._adapter.delete_domain_config(path.parsed.domain_name)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    # ------------------------------------------------------------------ user config

    async def get_user_config(
        self,
        path: PathParam[UserIdPathParam],
    ) -> APIResponse:
        """Get user-level app configuration."""
        result = await self._adapter.get_user_config(str(path.parsed.user_id))
        if result is None:
            raise web.HTTPNotFound(reason="User config not found")
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def upsert_user_config(
        self,
        path: PathParam[UserIdPathParam],
        body: BodyParam[UpsertUserConfigInput],
    ) -> APIResponse:
        """Create or update user-level app configuration."""
        result = await self._adapter.upsert_user_config(
            str(path.parsed.user_id), body.parsed.extra_config
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def delete_user_config(
        self,
        path: PathParam[UserIdPathParam],
    ) -> APIResponse:
        """Delete user-level app configuration."""
        result = await self._adapter.delete_user_config(str(path.parsed.user_id))
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    # ------------------------------------------------------------------ merged config

    async def get_merged_config(
        self,
        path: PathParam[UserIdPathParam],
    ) -> APIResponse:
        """Get merged app configuration for a user."""
        result = await self._adapter.get_merged_config(str(path.parsed.user_id))
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)
