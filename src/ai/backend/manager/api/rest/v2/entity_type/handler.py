"""REST v2 handler for the entity type registry domain."""

from __future__ import annotations

from http import HTTPStatus
from typing import TYPE_CHECKING

from ai.backend.common.api_handlers import APIResponse

if TYPE_CHECKING:
    from ai.backend.manager.api.adapters.entity.adapter import EntityAdapter


class V2EntityTypeHandler:
    """REST v2 handler exposing the entity types the manager has wired."""

    _adapter: EntityAdapter

    def __init__(self, *, adapter: EntityAdapter) -> None:
        self._adapter = adapter

    async def list_entity_types(self) -> APIResponse:
        """List every entity type a request may name."""
        payload = self._adapter.list_entity_types()
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=payload)
