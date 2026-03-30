from dataclasses import dataclass
from typing import override

from ai.backend.common.data.permission.types import EntityType
from ai.backend.manager.actions.action import BaseAction, BaseBatchAction
from ai.backend.manager.actions.action.scope import BaseScopeAction, BaseScopeActionResult
from ai.backend.manager.actions.action.single_entity import (
    BaseSingleEntityAction,
    BaseSingleEntityActionResult,
)
from ai.backend.manager.actions.action.types import FieldData


@dataclass
class ArtifactAction(BaseAction):
    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return EntityType.ARTIFACT


@dataclass
class ArtifactBatchAction(BaseBatchAction):
    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return EntityType.ARTIFACT


@dataclass
class ArtifactScopeAction(BaseScopeAction):
    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return EntityType.ARTIFACT


class ArtifactScopeActionResult(BaseScopeActionResult):
    pass


@dataclass
class ArtifactSingleEntityAction(BaseSingleEntityAction):
    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return EntityType.ARTIFACT

    @override
    def field_data(self) -> FieldData | None:
        return None


class ArtifactSingleEntityActionResult(BaseSingleEntityActionResult):
    pass
