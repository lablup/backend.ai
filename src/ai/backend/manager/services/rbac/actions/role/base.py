from dataclasses import dataclass
from typing import override

from ai.backend.common.data.permission.types import EntityType
from ai.backend.manager.actions.action import BaseAction


@dataclass
class RoleAction(BaseAction):
    """Base for granting a role to a user and taking it back.

    Still on the legacy base: the role domain's move to the v2 lineage is under way and
    these follow it there.
    """

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return EntityType.ROLE_ASSIGNMENT
