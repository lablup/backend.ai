import logging
from collections.abc import Mapping
from typing import Any

from ai.backend.common.exception import InvalidAPIParameters
from ai.backend.common.types import LegacyResourceSlotState as ResourceSlotState
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.repositories.resource_preset import ResourcePresetRepository
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
from ai.backend.manager.services.resource_preset.actions.modify_preset import (
    ModifyResourcePresetAction,
    ModifyResourcePresetActionResult,
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

        if not creator.resource_slots.has_intrinsic_slots():
            raise InvalidAPIParameters("ResourceSlot must have all intrinsic resource slots.")

        preset_data = await self._resource_preset_repository.create_preset_validated(creator)
        return CreateResourcePresetActionResult(resource_preset=preset_data)

    async def modify_preset(
        self, action: ModifyResourcePresetAction
    ) -> ModifyResourcePresetActionResult:
        name = action.name
        preset_id = action.id
        modifier = action.modifier

        if preset_id is None and name is None:
            raise InvalidAPIParameters("One of (`id` or `name`) parameter should not be null")

        if resource_slots := modifier.resource_slots.optional_value():
            if not resource_slots.has_intrinsic_slots():
                raise InvalidAPIParameters("ResourceSlot must have all intrinsic resource slots.")

        preset_data = await self._resource_preset_repository.modify_preset_validated(
            preset_id, name, modifier
        )

        return ModifyResourcePresetActionResult(resource_preset=preset_data)

    async def delete_preset(
        self, action: DeleteResourcePresetAction
    ) -> DeleteResourcePresetActionResult:
        name = action.name
        preset_id = action.id

        if preset_id is None and name is None:
            raise InvalidAPIParameters("One of (`id` or `name`) parameter should not be null")

        preset_data = await self._resource_preset_repository.delete_preset_validated(
            preset_id, name
        )

        return DeleteResourcePresetActionResult(resource_preset=preset_data)

    async def list_presets(self, action: ListResourcePresetsAction) -> ListResourcePresetsResult:
        preset_data_list = await self._resource_preset_repository.list_presets(action.scaling_group)

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

    async def check_presets(
        self, action: CheckResourcePresetsAction
    ) -> CheckResourcePresetsActionResult:
        result = await self._resource_preset_repository.check_presets(
            access_key=action.access_key,
            user_id=action.user_id,
            group_name=action.group,
            domain_name=action.domain_name,
            resource_policy=action.resource_policy,
            scaling_group=action.scaling_group,
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
        for sgname, sg_data in result.scaling_groups.items():
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
            scaling_group_remaining=result.scaling_group_remaining,
            scaling_groups=per_sgroup_dict,
        )
