from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.domain import DOMAIN_SCOPE_TYPE, DomainID
from ai.backend.common.data.entity.project import PROJECT_ENTITY_TYPE
from ai.backend.common.data.entity.types import EntityType, ScopeRef
from ai.backend.manager.actions.v2.ops.base import CreateRoleManagedEntityOpsAction
from ai.backend.manager.data.project.types import ProjectData
from ai.backend.manager.models.project.creators import ProjectCreator
from ai.backend.manager.models.project.row import ProjectRow


@dataclass(frozen=True)
class CreateProjectAction(CreateRoleManagedEntityOpsAction[ProjectRow, ProjectData]):
    """Register a project under a domain."""

    domain_id: DomainID
    creator: ProjectCreator

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return PROJECT_ENTITY_TYPE

    @override
    def scope_targets(self) -> Sequence[ScopeRef]:
        return (ScopeRef(scope_type=DOMAIN_SCOPE_TYPE, scope_id=self.domain_id),)

    @override
    @classmethod
    def action_name(cls) -> str:
        return "create_project"

    @override
    def to_creator(self) -> ProjectCreator:
        return self.creator
