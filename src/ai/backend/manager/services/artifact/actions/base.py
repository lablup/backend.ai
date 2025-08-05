from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.action import BaseAction, BaseBatchAction


@dataclass
class ArtifactAction(BaseAction):
    @override
    @classmethod
    def entity_type(cls) -> str:
        return "artifact"


@dataclass
class ArtifactBatchAction(BaseBatchAction):
    @override
    @classmethod
    def entity_type(cls) -> str:
        return "artifact"
