from dataclasses import dataclass
from typing import override

from ai.backend.common.data.permission.types import RBACElementType
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.artifact.types import ArtifactData
from ai.backend.manager.data.permission.types import RBACElementRef
from ai.backend.manager.models.artifact import ArtifactRow
from ai.backend.manager.repositories.base.updater import Updater
from ai.backend.manager.services.artifact.actions.base import (
    ArtifactSingleEntityAction,
    ArtifactSingleEntityActionResult,
)


@dataclass
class UpdateArtifactAction(ArtifactSingleEntityAction):
    updater: Updater[ArtifactRow]

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE

    @override
    def target_entity_id(self) -> str:
        return str(self.updater.pk_value)

    @override
    def target_element(self) -> RBACElementRef:
        return RBACElementRef(RBACElementType.ARTIFACT, str(self.updater.pk_value))


@dataclass
class UpdateArtifactActionResult(ArtifactSingleEntityActionResult):
    result: ArtifactData

    @override
    def target_entity_id(self) -> str:
        return str(self.result.id)
