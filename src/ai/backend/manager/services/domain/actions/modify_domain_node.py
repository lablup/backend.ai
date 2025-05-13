from dataclasses import dataclass, field
from typing import Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.services.domain.actions.base import DomainAction
from ai.backend.manager.services.domain.types import DomainData, DomainNodeModifier, UserInfo


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
    domain_data: Optional[DomainData]
    success: bool
    description: Optional[str]

    @override
    def entity_id(self):
        return self.domain_data.name if self.domain_data is not None else None
