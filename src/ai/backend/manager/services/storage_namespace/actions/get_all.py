import uuid
from dataclasses import dataclass
from typing import Dict, List, Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.services.storage_namespace.actions.base import StorageNamespaceAction


@dataclass
class GetAllNamespacesAction(StorageNamespaceAction):
    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "get_all"


@dataclass
class GetAllNamespacesActionResult(BaseActionResult):
    result: Dict[uuid.UUID, List[str]]

    @override
    def entity_id(self) -> Optional[str]:
        return None
