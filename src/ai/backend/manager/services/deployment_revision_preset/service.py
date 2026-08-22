from __future__ import annotations

from ai.backend.manager.actions.v2.ops.result import EntityOpsResult
from ai.backend.manager.data.deployment_revision_preset.types import DeploymentRevisionPresetData
from ai.backend.manager.repositories.deployment_revision_preset.repository import (
    DeploymentPresetRepository,
)
from ai.backend.manager.services.deployment_revision_preset.actions.update import (
    UpdateDeploymentPresetAction,
)

__all__ = ("DeploymentPresetService",)


class DeploymentPresetService:
    """The one operation that reaches past a single spec.

    An update may restate the preset's slots, which is two tables in one transaction.
    Everything else runs straight against ops.
    """

    _repository: DeploymentPresetRepository

    def __init__(self, repository: DeploymentPresetRepository) -> None:
        self._repository = repository

    async def update(
        self, action: UpdateDeploymentPresetAction
    ) -> EntityOpsResult[DeploymentRevisionPresetData]:
        data = await self._repository.update(action.to_updater(), action.slot_creators)
        return EntityOpsResult(data=data)
