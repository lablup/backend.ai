from typing import override

from ai.backend.common.data.permission.types import EntityType
from ai.backend.manager.actions.action import BaseAction
from ai.backend.manager.actions.action.scope import BaseScopeAction, BaseScopeActionResult
from ai.backend.manager.actions.action.single_entity import (
    BaseSingleEntityAction,
    BaseSingleEntityActionResult,
)
from ai.backend.manager.actions.action.types import FieldData


class DeploymentReplicaBaseAction(BaseAction):
    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return EntityType.DEPLOYMENT_REPLICA


class DeploymentReplicaScopeAction(BaseScopeAction):
    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return EntityType.DEPLOYMENT_REPLICA


class DeploymentReplicaScopeActionResult(BaseScopeActionResult):
    pass


class DeploymentReplicaSingleEntityAction(BaseSingleEntityAction):
    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return EntityType.DEPLOYMENT_REPLICA

    @override
    def field_data(self) -> FieldData | None:
        return None


class DeploymentReplicaSingleEntityActionResult(BaseSingleEntityActionResult):
    pass
