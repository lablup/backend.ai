from dataclasses import dataclass
from typing import Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.models.container_registry import ContainerRegistryRow
from ai.backend.manager.services.image.base import ImageAction


@dataclass
class ClearImagesAction(ImageAction):
    registry: str
    project: str

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    def operation_type(self):
        return "clear"


@dataclass
class ClearImagesActionResult(BaseActionResult):
    registry_row: ContainerRegistryRow

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.registry_row.id)


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
