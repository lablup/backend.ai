from dataclasses import dataclass, field
from typing import Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.services.domain.actions.base import DomainAction
from ai.backend.manager.services.domain.types import DomainData, DomainModifier


@dataclass
class ModifyDomainAction(DomainAction):
    domain_name: str
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
    domain_data: Optional[DomainData]
    success: bool = field(compare=False)
    description: Optional[str] = field(compare=False)

    @override
    def entity_id(self) -> Optional[str]:
        return self.domain_data.name if self.domain_data is not None else None
