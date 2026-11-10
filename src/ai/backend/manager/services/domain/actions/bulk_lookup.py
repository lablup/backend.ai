from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.domain import DomainEntityType, DomainID, DomainName
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.v2.ops.base import BulkLookupEntityOpsAction
from ai.backend.manager.models.domain.lookups import DomainNamesLookup
from ai.backend.manager.services.domain.actions.lookup import DomainNameKey


@dataclass
class BulkLookupDomainsAction(BulkLookupEntityOpsAction[DomainName, DomainID]):
    """Resolve several names into the domains they name."""

    names: Sequence[DomainName]

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return DomainEntityType()

    @override
    @classmethod
    def action_name(cls) -> str:
        return "bulk_lookup_domains"

    @override
    def keys(self) -> Sequence[DomainName]:
        return tuple(self.names)

    @override
    def to_lookup_key(self, key: DomainName) -> DomainNameKey:
        return DomainNameKey(name=key)

    @override
    def to_lookup(self) -> DomainNamesLookup:
        return DomainNamesLookup()
