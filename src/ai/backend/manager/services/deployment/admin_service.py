from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from ai.backend.logging.utils import BraceStyleAdapter

from .actions.sync_model_definitions import (
    SyncModelDefinitionsAction,
    SyncModelDefinitionsActionResult,
)

if TYPE_CHECKING:
    from ai.backend.manager.repositories.deployment.admin_repository import (
        DeploymentAdminRepository,
    )

log = BraceStyleAdapter(logging.getLogger(__name__))


class DeploymentAdminService:
    """Service for admin-only deployment maintenance operations."""

    _repository: DeploymentAdminRepository

    def __init__(self, repository: DeploymentAdminRepository) -> None:
        self._repository = repository

    async def sync_model_definitions(
        self, action: SyncModelDefinitionsAction
    ) -> SyncModelDefinitionsActionResult:
        """Sync model_definition from vfolder storage for all revisions where it differs from the vfolder file."""
        results = await self._repository.sync_model_definitions()
        updated = sum(1 for r in results if r.success)
        failed = sum(1 for r in results if not r.success)
        log.info("Model definition sync complete: updated={}, failed={}", updated, failed)
        return SyncModelDefinitionsActionResult(results=results)
