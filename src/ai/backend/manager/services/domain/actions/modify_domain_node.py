from dataclasses import dataclass, field
from typing import Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.domain.types import DomainData, DomainNodeModifier, UserInfo
from ai.backend.manager.services.domain.actions.base import DomainAction


@dataclass
class ModifyDomainNodeAction(DomainAction):
    name: str
    user_info: UserInfo
    sgroups_to_add: Optional[set[str]] = None
    sgroups_to_remove: Optional[set[str]] = None
    modifier: DomainNodeModifier = field(default_factory=DomainNodeModifier)

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "modify"


@dataclass
class ModifyDomainNodeActionResult(BaseActionResult):
    domain_data: DomainData

    @override
    def entity_id(self):
        return self.domain_data.name
