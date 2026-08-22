import logging
from collections.abc import Mapping
from typing import Any, cast

from ai.backend.common.exception import InvalidAPIParameters
from ai.backend.common.types import LegacyResourceSlotState as ResourceSlotState
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.repositories.resource_preset import ResourcePresetRepository
from ai.backend.manager.repositories.resource_preset.creators import ResourcePresetCreatorSpec
from ai.backend.manager.repositories.resource_preset.updaters import ResourcePresetUpdaterSpec
from ai.backend.manager.services.resource_preset.actions.check_presets import (
    CheckResourcePresetsAction,
    CheckResourcePresetsActionResult,
)
from ai.backend.manager.services.resource_preset.actions.create_preset import (
    CreateResourcePresetAction,
    CreateResourcePresetActionResult,
)
from ai.backend.manager.services.resource_preset.actions.delete_preset import (
    DeleteResourcePresetAction,
    DeleteResourcePresetActionResult,
)
from ai.backend.manager.services.resource_preset.actions.list_presets import (
    ListResourcePresetsAction,
    ListResourcePresetsResult,
)
from ai.backend.manager.services.resource_preset.actions.search_presets import (
    SearchResourcePresetsV2Action,
    SearchResourcePresetsV2ActionResult,
)
from ai.backend.manager.services.resource_preset.actions.update_preset import (
    UpdateResourcePresetAction,
    UpdateResourcePresetActionResult,
)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class ResourcePresetService:
    _resource_preset_repository: ResourcePresetRepository

    def __init__(
        self,
        resource_preset_repository: ResourcePresetRepository,
    ) -> None:
        self._resource_preset_repository = resource_preset_repository

    async def create_preset(
        self, action: CreateResourcePresetAction
    ) -> CreateResourcePresetActionResult:
        creator = action.creator
        spec = cast(ResourcePresetCreatorSpec, creator.spec)

        if not spec.resource_slots.has_intrinsic_slots():
            raise InvalidAPIParameters("ResourceSlot must have all intrinsic resource slots.")

        preset_data = await self._resource_preset_repository.create_preset_validated(creator)
        return CreateResourcePresetActionResult(resource_preset=preset_data)

    async def update_preset(
        self, action: UpdateResourcePresetAction
    ) -> UpdateResourcePresetActionResult:
        spec = cast(ResourcePresetUpdaterSpec, action.updater.spec)
        if resource_slots := spec.resource_slots.optional_value():
            if not resource_slots.has_intrinsic_slots():
                raise InvalidAPIParameters("ResourceSlot must have all intrinsic resource slots.")

        action.updater.pk_value = action.preset_id
        preset_data = await self._resource_preset_repository.modify_preset_validated(action.updater)
        return UpdateResourcePresetActionResult(resource_preset=preset_data)

    async def delete_preset(
        self, action: DeleteResourcePresetAction
    ) -> DeleteResourcePresetActionResult:
        preset_data = await self._resource_preset_repository.delete_preset_validated(
            action.preset_id, None
        )
        return DeleteResourcePresetActionResult(resource_preset=preset_data)

    async def list_presets(self, action: ListResourcePresetsAction) -> ListResourcePresetsResult:
        preset_data_list = await self._resource_preset_repository.list_presets(
            action.resource_group
        )

        presets = []
        for preset_data in preset_data_list:
            preset_slots = preset_data.resource_slots.normalize_slots(ignore_unknown=True)
            presets.append({
                "id": str(preset_data.id),
                "name": preset_data.name,
                "shared_memory": str(preset_data.shared_memory)
                if preset_data.shared_memory
                else None,
                "resource_slots": preset_slots.to_json(),
            })

        return ListResourcePresetsResult(presets=presets)

    async def search_presets_v2(
        self,
        action: SearchResourcePresetsV2Action,
    ) -> SearchResourcePresetsV2ActionResult:
        """Search resource presets with filter/order/pagination."""
        result = await self._resource_preset_repository.search_presets(action.querier)
        return SearchResourcePresetsV2ActionResult(
            presets=result.items,
            total_count=result.total_count,
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
        )

    async def check_presets(
        self, action: CheckResourcePresetsAction
    ) -> CheckResourcePresetsActionResult:
        result = await self._resource_preset_repository.check_presets(
            access_key=action.access_key,
            user_id=action.user_id,
            group_name=action.group,
            domain_name=action.domain_name,
            resource_policy=action.resource_policy,
            resource_group=action.resource_group,
        )

        # Convert repository result to action result
        # Process presets to JSON format
        presets: list[Mapping[str, Any]] = []
        for preset_data in result.presets:
            preset_slots = preset_data.preset.resource_slots.normalize_slots(ignore_unknown=True)
            presets.append({
                "id": str(preset_data.preset.id),
                "name": preset_data.preset.name,
                "resource_slots": preset_slots.to_json(),
                "shared_memory": (
                    str(preset_data.preset.shared_memory)
                    if preset_data.preset.shared_memory is not None
                    else None
                ),
                "allocatable": preset_data.allocatable,
            })

        # Convert per scaling group data to appropriate format
        per_sgroup_dict = {}
        for sgname, sg_data in result.resource_groups.items():
            per_sgroup_dict[sgname] = {
                ResourceSlotState.OCCUPIED: sg_data.using,
                ResourceSlotState.AVAILABLE: sg_data.remaining,
            }

        return CheckResourcePresetsActionResult(
            presets=presets,
            keypair_limits=result.keypair_limits,
            keypair_using=result.keypair_using,
            keypair_remaining=result.keypair_remaining,
            group_limits=result.group_limits,
            group_using=result.group_using,
            group_remaining=result.group_remaining,
            domain_limits=result.domain_limits,
            resource_group_remaining=result.resource_group_remaining,
            resource_groups=per_sgroup_dict,
        )
