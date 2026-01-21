from dataclasses import dataclass
from typing import Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.container_registry.types import ContainerRegistryData
from ai.backend.manager.services.container_registry.actions.base import ContainerRegistryAction


@dataclass
class ClearImagesAction(ContainerRegistryAction):
    registry: str
    project: Optional[str]

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "clear"


@dataclass
class ClearImagesActionResult(BaseActionResult):
    registry: ContainerRegistryData

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.registry.id)


# @dataclass
# class ClearImagesBatchAction(ImageAction):
#     registry: str

#     @override
#     def entity_id(self) -> Optional[str]:
#         return None

#     @override
#     def operation_type(self):
#         return "clear_multi"


# @dataclass
# class ClearImagesBatchActionResult(BaseActionResult):
#     registry_row: ContainerRegistryRow

#     @override
#     def entity_id(self) -> Optional[str]:
#         return None
