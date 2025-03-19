from dataclasses import dataclass
from typing import Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.services.image.base import ImageAction


@dataclass
class UnloadImageAction(ImageAction):
    references: list[str]
    agents: list[str]

    @override
    def entity_id(self) -> str:
        # TODO: ?
        return f"{self.references} on {self.agents}"

    @override
    def operation_type(self):
        return "unload_image"


@dataclass
class UnloadImageActionResult(BaseActionResult):
    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    def status(self) -> str:
        return "success"

    @override
    def description(self) -> Optional[str]:
        return ""

    # def __eq__(self, other: Any) -> bool:
    #     if not isinstance(other, AliasImageActionResult):
    #         return False
    #     # TODO: 여기선 id로 비교못할 듯.
    #     return self.image_alias.alias == other.image_alias.alias
