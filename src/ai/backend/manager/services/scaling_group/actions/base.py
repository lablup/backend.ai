from typing import override

from ai.backend.common.data.permission.types import EntityType
from ai.backend.manager.actions.action import BaseAction
from ai.backend.manager.actions.action.scope import BaseScopeAction, BaseScopeActionResult
from ai.backend.manager.actions.action.single_entity import (
    BaseSingleEntityAction,
    BaseSingleEntityActionResult,
)


class ScalingGroupAction(BaseAction):
    """Base action class for scaling group operations."""

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return EntityType.RESOURCE_GROUP


class ScalingGroupScopeAction(BaseScopeAction):
    """Base action class for scaling group scope operations."""

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return EntityType.RESOURCE_GROUP


class ScalingGroupScopeActionResult(BaseScopeActionResult):
    """Base result class for scaling group scope operations."""

    pass


class ScalingGroupSingleEntityAction(BaseSingleEntityAction):
    """Base action class for scaling group single entity operations."""

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return EntityType.RESOURCE_GROUP


class ScalingGroupSingleEntityActionResult(BaseSingleEntityActionResult):
    """Base result class for scaling group single entity operations."""

    pass
