from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.action import BaseAction, BaseBatchAction


@dataclass
class ArtifactRegistryAction(BaseAction):
    @override
    @classmethod
    def entity_type(cls) -> str:
        return "artifact_registry"


@dataclass
class ArtifactBatchRegistryAction(BaseBatchAction):
    @override
    @classmethod
    def entity_type(cls) -> str:
        return "artifact_registry"
