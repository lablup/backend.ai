import logging

from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.repositories.runtime_variant.repository import RuntimeVariantRepository
from ai.backend.manager.services.runtime_variant.actions.create import (
    CreateRuntimeVariantAction,
    CreateRuntimeVariantActionResult,
)
from ai.backend.manager.services.runtime_variant.actions.delete import (
    DeleteRuntimeVariantAction,
    DeleteRuntimeVariantActionResult,
)
from ai.backend.manager.services.runtime_variant.actions.search import (
    SearchRuntimeVariantsAction,
    SearchRuntimeVariantsActionResult,
)
from ai.backend.manager.services.runtime_variant.actions.update import (
    UpdateRuntimeVariantAction,
    UpdateRuntimeVariantActionResult,
)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class RuntimeVariantService:
    _repository: RuntimeVariantRepository

    def __init__(self, repository: RuntimeVariantRepository) -> None:
        self._repository = repository

    async def create(self, action: CreateRuntimeVariantAction) -> CreateRuntimeVariantActionResult:
        data = await self._repository.create(action.creator)
        return CreateRuntimeVariantActionResult(runtime_variant=data)

    async def update(self, action: UpdateRuntimeVariantAction) -> UpdateRuntimeVariantActionResult:
        action.updater.pk_value = action.id
        data = await self._repository.update(action.updater)
        return UpdateRuntimeVariantActionResult(runtime_variant=data)

    async def delete(self, action: DeleteRuntimeVariantAction) -> DeleteRuntimeVariantActionResult:
        data = await self._repository.delete(action.id)
        return DeleteRuntimeVariantActionResult(runtime_variant=data)

    async def search(
        self, action: SearchRuntimeVariantsAction
    ) -> SearchRuntimeVariantsActionResult:
        items, total_count, has_next_page, has_previous_page = await self._repository.search(
            action.querier
        )
        return SearchRuntimeVariantsActionResult(
            items=items,
            total_count=total_count,
            has_next_page=has_next_page,
            has_previous_page=has_previous_page,
        )
