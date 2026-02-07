from typing import override

from ai.backend.manager.actions.action import BaseAction


class ArtifactStorageAction(BaseAction):
    @override
    @classmethod
    def entity_type(cls) -> str:
        return "artifact_storage"
