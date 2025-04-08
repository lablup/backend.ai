from dataclasses import dataclass, field
from typing import Any, Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.services.domain.actions.base import DomainAction
from ai.backend.manager.services.domain.types import DomainData, DomainNodeModifier, UserInfo
from ai.backend.manager.types import OptionalState


@dataclass
class ModifyDomainNodeAction(DomainAction):
    name: str
    user_info: UserInfo
    modifier: DomainNodeModifier = field(default_factory=DomainNodeModifier)
    sgroups_to_add: OptionalState[set[str]] = field(
        default_factory=lambda: OptionalState.nop("scaling_groups")
    )
    sgroups_to_remove: OptionalState[set[str]] = field(
        default_factory=lambda: OptionalState.nop("scaling_groups")
    )

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    def operation_type(self) -> str:
        return "modify"

    def get_modified_fields(self) -> dict[str, Any]:
        return self.modifier.get_modified_fields()


@dataclass
class ModifyDomainNodeActionResult(BaseActionResult):
    domain_data: Optional[DomainData]
    success: bool
    description: Optional[str]

    @override
    def entity_id(self):
        return self.domain_data.name if self.domain_data is not None else None
