import logging
from typing import cast

from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.repositories.deployment_revision_preset.creators import (
    DeploymentRevisionPresetCreatorSpec,
)
from ai.backend.manager.repositories.deployment_revision_preset.repository import (
    DeploymentRevisionPresetRepository,
)
from ai.backend.manager.services.deployment_revision_preset.actions.create import (
    CreateDeploymentRevisionPresetAction,
    CreateDeploymentRevisionPresetActionResult,
)
from ai.backend.manager.services.deployment_revision_preset.actions.delete import (
    DeleteDeploymentRevisionPresetAction,
    DeleteDeploymentRevisionPresetActionResult,
)
from ai.backend.manager.services.deployment_revision_preset.actions.search import (
    SearchDeploymentRevisionPresetsAction,
    SearchDeploymentRevisionPresetsActionResult,
)
from ai.backend.manager.services.deployment_revision_preset.actions.search_resource_slots import (
    SearchPresetResourceSlotsAction,
    SearchPresetResourceSlotsActionResult,
)
from ai.backend.manager.services.deployment_revision_preset.actions.update import (
    UpdateDeploymentRevisionPresetAction,
    UpdateDeploymentRevisionPresetActionResult,
)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class DeploymentRevisionPresetService:
    _repository: DeploymentRevisionPresetRepository

    def __init__(self, repository: DeploymentRevisionPresetRepository) -> None:
        self._repository = repository

    async def create(
        self, action: CreateDeploymentRevisionPresetAction
    ) -> CreateDeploymentRevisionPresetActionResult:
        spec = cast(DeploymentRevisionPresetCreatorSpec, action.creator.spec)
        next_rank = await self._repository.get_next_rank(spec.runtime_variant_id)
        spec.rank = next_rank

        data = await self._repository.create(action.creator)
        return CreateDeploymentRevisionPresetActionResult(preset=data)

    async def update(
        self, action: UpdateDeploymentRevisionPresetAction
    ) -> UpdateDeploymentRevisionPresetActionResult:
        action.updater.pk_value = action.id
        data = await self._repository.update(action.updater)
        return UpdateDeploymentRevisionPresetActionResult(preset=data)

    async def delete(
        self, action: DeleteDeploymentRevisionPresetAction
    ) -> DeleteDeploymentRevisionPresetActionResult:
        data = await self._repository.delete(action.id)
        return DeleteDeploymentRevisionPresetActionResult(preset=data)

    async def search(
        self, action: SearchDeploymentRevisionPresetsAction
    ) -> SearchDeploymentRevisionPresetsActionResult:
        items, total_count, has_next_page, has_previous_page = await self._repository.search(
            action.querier
        )
        return SearchDeploymentRevisionPresetsActionResult(
            items=items,
            total_count=total_count,
            has_next_page=has_next_page,
            has_previous_page=has_previous_page,
        )

    async def search_resource_slots(
        self, action: SearchPresetResourceSlotsAction
    ) -> SearchPresetResourceSlotsActionResult:
        """Search resource slots allocated to a deployment revision preset."""
        (
            items,
            total_count,
            has_next_page,
            has_previous_page,
        ) = await self._repository.search_resource_slots(action.preset_id, action.querier)
        return SearchPresetResourceSlotsActionResult(
            items=items,
            total_count=total_count,
            has_next_page=has_next_page,
            has_previous_page=has_previous_page,
        )
