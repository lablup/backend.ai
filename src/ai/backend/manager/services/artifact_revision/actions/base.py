from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.action import BaseAction, BaseBatchAction


@dataclass
class ArtifactRevisionAction(BaseAction):
    @override
    @classmethod
    def entity_type(cls) -> str:
        return "artifact_revision"


@dataclass
class ArtifactRevisionBatchAction(BaseBatchAction):
    @override
    @classmethod
    def entity_type(cls) -> str:
        return "artifact_revision"
