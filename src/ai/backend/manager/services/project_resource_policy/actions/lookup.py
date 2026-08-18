from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

from ai.backend.common.data.entity.resource_policy import (
    PROJECT_RESOURCE_POLICY_ENTITY_TYPE,
)
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.v2.lookup.base import LookupKey
from ai.backend.manager.actions.v2.ops.base import LookupEntityOpsAction
from ai.backend.manager.data.resource.types import ProjectResourcePolicyData
from ai.backend.manager.models.resource_policy.row import ProjectResourcePolicyRow
from ai.backend.manager.repositories.project_resource_policy.lookups import (
    ProjectResourcePolicyNameLookup,
)


@dataclass(frozen=True)
class ProjectResourcePolicyNameKey(LookupKey):
    """The catalog name a caller passes instead of the policy's id."""

    name: str

    @override
    def kind(self) -> str:
        return "project_resource_policy_name"

    @override
    def to_dict(self) -> dict[str, Any]:
        return {"name": self.name}


@dataclass
class LookupProjectResourcePolicyAction(
    LookupEntityOpsAction[ProjectResourcePolicyRow, ProjectResourcePolicyData]
):
    """Resolve a project resource policy's name into the policy it names."""

    name: str

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return PROJECT_RESOURCE_POLICY_ENTITY_TYPE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "lookup_project_resource_policy"

    @override
    def lookup_key(self) -> ProjectResourcePolicyNameKey:
        return ProjectResourcePolicyNameKey(name=self.name)

    @override
    def to_lookup(self) -> ProjectResourcePolicyNameLookup:
        return ProjectResourcePolicyNameLookup(name=self.name)
