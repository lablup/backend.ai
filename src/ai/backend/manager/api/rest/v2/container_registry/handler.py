"""REST v2 handler for the container registry domain."""

from __future__ import annotations

import logging
from http import HTTPStatus
from typing import TYPE_CHECKING, Final

from ai.backend.common.api_handlers import APIResponse, BodyParam
from ai.backend.common.dto.manager.v2.container_registry.request import (
    AdminSearchContainerRegistriesInput,
)
from ai.backend.logging import BraceStyleAdapter

if TYPE_CHECKING:
    from ai.backend.manager.api.adapters.container_registry import ContainerRegistryAdapter

log: Final = BraceStyleAdapter(logging.getLogger(__spec__.name))


class V2ContainerRegistryHandler:
    """REST v2 handler for container registry operations."""

    def __init__(self, *, adapter: ContainerRegistryAdapter) -> None:
        self._adapter = adapter

    async def admin_search_container_registries(
        self,
        body: BodyParam[AdminSearchContainerRegistriesInput],
    ) -> APIResponse:
        """Search container registries with admin scope."""
        result = await self._adapter.admin_search(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)
