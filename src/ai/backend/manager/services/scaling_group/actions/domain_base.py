from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.domain import DomainID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.v2.single_entity.base import BaseSingleEntityAction


@dataclass(frozen=True)
class ScalingGroupDomainAction(BaseSingleEntityAction):
    """Base for an operation on the resource groups a domain may schedule on.

    The domain answers for it: what changes is which groups that domain reaches.
    """

    domain_id: DomainID

    @override
    def entity_id(self) -> EntityIdentifier:
        return self.domain_id
