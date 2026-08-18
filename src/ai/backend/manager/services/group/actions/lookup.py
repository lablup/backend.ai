from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

from ai.backend.common.data.entity.domain import DomainName
from ai.backend.common.data.entity.project import PROJECT_ENTITY_TYPE
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.v2.lookup.base import LookupKey
from ai.backend.manager.actions.v2.ops.base import LookupEntityOpsAction
from ai.backend.manager.data.group.types import GroupData
from ai.backend.manager.models.group.lookups import ProjectNameInDomainLookup
from ai.backend.manager.models.group.row import GroupRow


@dataclass(frozen=True)
class ProjectNameInDomainKey(LookupKey):
    """The name a caller passes instead of the project's id, with the domain it is in."""

    domain_name: DomainName
    project_name: str

    @override
    def kind(self) -> str:
        return "project_name_in_domain"

    @override
    def to_dict(self) -> dict[str, Any]:
        return {"domain_name": str(self.domain_name), "project_name": self.project_name}


@dataclass
class LookupProjectAction(LookupEntityOpsAction[GroupRow, GroupData]):
    """Resolve a project's domain-scoped name into the project it names."""

    domain_name: DomainName
    project_name: str

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return PROJECT_ENTITY_TYPE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "lookup_project"

    @override
    def lookup_key(self) -> ProjectNameInDomainKey:
        return ProjectNameInDomainKey(domain_name=self.domain_name, project_name=self.project_name)

    @override
    def to_lookup(self) -> ProjectNameInDomainLookup:
        return ProjectNameInDomainLookup(
            domain_name=self.domain_name, project_name=self.project_name
        )
