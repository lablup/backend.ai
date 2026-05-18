from __future__ import annotations

from ai.backend.manager.repositories.deployment.admin_repository import (
    DeploymentAdminRepository,
)
from ai.backend.manager.services.deployment.actions.admin_search_deployments import (
    AdminSearchDeploymentsAction,
    AdminSearchDeploymentsActionResult,
)

__all__ = ("DeploymentAdminService",)


class DeploymentAdminService:
    """Admin (no-scope) service operations for deployments.

    Holds the call sites that are not bounded by a project / user / domain
    scope (admin search, DataLoader batch lookups). Scoped operations live
    on :class:`DeploymentService`.
    """

    _admin_repository: DeploymentAdminRepository

    def __init__(self, admin_repository: DeploymentAdminRepository) -> None:
        self._admin_repository = admin_repository

    async def admin_search_deployments(
        self, action: AdminSearchDeploymentsAction
    ) -> AdminSearchDeploymentsActionResult:
        """Search every deployment without a scope filter."""
        result = await self._admin_repository.admin_search_deployments(action.querier)
        return AdminSearchDeploymentsActionResult(
            data=result.items,
            total_count=result.total_count,
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
        )
