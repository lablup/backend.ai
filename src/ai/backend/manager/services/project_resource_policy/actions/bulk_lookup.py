from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.resource_policy import (
    ProjectResourcePolicyEntityType,
    ProjectResourcePolicyUUID,
)
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.v2.ops.base import BulkLookupEntityOpsAction
from ai.backend.manager.models.resource_policy.lookups import ProjectResourcePolicyNamesLookup
from ai.backend.manager.services.project_resource_policy.actions.lookup import (
    ProjectResourcePolicyNameKey,
)


@dataclass
class BulkLookupProjectResourcePoliciesAction(
    BulkLookupEntityOpsAction[str, ProjectResourcePolicyUUID]
):
    """Resolve several project resource policy names into the policies they name."""

    names: Sequence[str]

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return ProjectResourcePolicyEntityType()

    @override
    @classmethod
    def action_name(cls) -> str:
        return "bulk_lookup_project_resource_policies"

    @override
    def keys(self) -> Sequence[str]:
        return tuple(self.names)

    @override
    def to_lookup_key(self, key: str) -> ProjectResourcePolicyNameKey:
        return ProjectResourcePolicyNameKey(name=key)

    @override
    def to_lookup(self) -> ProjectResourcePolicyNamesLookup:
        return ProjectResourcePolicyNamesLookup()
