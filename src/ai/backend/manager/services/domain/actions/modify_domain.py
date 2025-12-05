from dataclasses import dataclass, field
from typing import Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.domain.types import DomainData, DomainModifier, UserInfo
from ai.backend.manager.services.domain.actions.base import DomainAction


@dataclass
class ModifyDomainAction(DomainAction):
    domain_name: str
    user_info: UserInfo
    modifier: DomainModifier = field(default_factory=DomainModifier)

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "modify"

    def get_modified_fields(self):
        return self.modifier.fields_to_update()


@dataclass
class ModifyDomainActionResult(BaseActionResult):
    domain_data: DomainData

    @override
    def entity_id(self) -> Optional[str]:
        return self.domain_data.name
