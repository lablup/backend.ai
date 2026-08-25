"""REST v2 handler for the scope operation catalog."""

from __future__ import annotations

from http import HTTPStatus
from typing import TYPE_CHECKING

from ai.backend.common.api_handlers import APIResponse

if TYPE_CHECKING:
    from ai.backend.manager.api.adapters.scope_operation.adapter import ScopeOperationAdapter


class V2ScopeOperationHandler:
    """REST v2 handler exposing the scope operations the manager has wired."""

    _adapter: ScopeOperationAdapter

    def __init__(self, *, adapter: ScopeOperationAdapter) -> None:
        self._adapter = adapter

    async def list_scope_operations(self) -> APIResponse:
        """List every operation the wiring targets by scope."""
        payload = self._adapter.list_scope_operations()
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=payload)
