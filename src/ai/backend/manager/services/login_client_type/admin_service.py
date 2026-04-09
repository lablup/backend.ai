from __future__ import annotations

from ai.backend.manager.repositories.login_client_type.admin_repository import (
    LoginClientTypeAdminRepository,
)
from ai.backend.manager.services.login_client_type.actions.search import (
    AdminSearchLoginClientTypesAction,
    SearchLoginClientTypesActionResult,
)

__all__ = ("LoginClientTypeAdminService",)


class LoginClientTypeAdminService:
    _admin_repository: LoginClientTypeAdminRepository

    def __init__(self, admin_repository: LoginClientTypeAdminRepository) -> None:
        self._admin_repository = admin_repository

    async def search(
        self, action: AdminSearchLoginClientTypesAction
    ) -> SearchLoginClientTypesActionResult:
        """Search all login client types without scope restriction (admin-only)."""
        result = await self._admin_repository.search(querier=action.querier)
        return SearchLoginClientTypesActionResult(
            items=result.items,
            total_count=result.total_count,
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
        )
