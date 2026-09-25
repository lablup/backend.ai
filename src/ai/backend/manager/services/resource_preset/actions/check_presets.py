import uuid
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, override

from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.common.types import (
    AccessKey,
    SlotQuantity,
)
from ai.backend.common.types import (
    LegacyResourceSlotState as ResourceSlotState,
)
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.actions.v2.scope.result import BaseScopeActionResult
from ai.backend.manager.services.resource_preset.actions.scope_base import (
    ResourcePresetScopeAction,
)


@dataclass
class CheckResourcePresetsAction(ResourcePresetScopeAction):
    """List the presets the named scopes offer, against the caller's own limits.

    The occupancy it adds is the caller's own: the keypair, group and domain it reports
    on are theirs.
    """

    access_key: AccessKey
    resource_policy: Mapping[str, Any]
    domain_name: str
    user_id: uuid.UUID
    group: str
    resource_group: str | None

    @override
    @classmethod
    def action_name(cls) -> str:
        return "check_resource_presets"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH


@dataclass
class CheckResourcePresetsActionResult(BaseScopeActionResult):
    presets: list[Mapping[str, Any]]
    keypair_limits: list[SlotQuantity]
    keypair_using: list[SlotQuantity]
    keypair_remaining: list[SlotQuantity]
    group_limits: list[SlotQuantity]
    group_using: list[SlotQuantity]
    group_remaining: list[SlotQuantity]
    resource_group_remaining: list[SlotQuantity]
    resource_groups: Mapping[str, Mapping[ResourceSlotState, list[SlotQuantity]]]

    # TODO: Should return preset row ids after changing to batching.

    @override
    def entity_ids(self) -> Sequence[EntityIdentifier]:
        return ()
