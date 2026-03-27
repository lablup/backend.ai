"""REST v2 handler for the artifact registry domain."""

from __future__ import annotations

import logging
from http import HTTPStatus
from typing import TYPE_CHECKING, Final

from ai.backend.common.api_handlers import APIResponse, PathParam
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.api.rest.v2.path_params import RegistryIdPathParam

if TYPE_CHECKING:
    from ai.backend.manager.api.adapters.artifact_registry import ArtifactRegistryAdapter

log: Final = BraceStyleAdapter(logging.getLogger(__spec__.name))


class V2ArtifactRegistryHandler:
    """REST v2 handler for artifact registry metadata operations."""

    def __init__(self, *, adapter: ArtifactRegistryAdapter) -> None:
        self._adapter = adapter

    async def get_registry_meta(
        self,
        path: PathParam[RegistryIdPathParam],
    ) -> APIResponse:
        """Get metadata for a single artifact registry by ID."""
        result = await self._adapter.get_registry_meta(
            registry_id=path.parsed.registry_id,
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)
