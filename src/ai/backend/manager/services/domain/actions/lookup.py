from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

from ai.backend.common.data.entity.domain import DOMAIN_ENTITY_TYPE, DomainName
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.v2.lookup.base import LookupKey
from ai.backend.manager.actions.v2.ops.base import LookupEntityOpsAction
from ai.backend.manager.data.domain.types import DomainData
from ai.backend.manager.models.domain.lookups import DomainNameLookup
from ai.backend.manager.models.domain.row import DomainRow


@dataclass(frozen=True)
class DomainNameKey(LookupKey):
    """The name a caller passes instead of the domain's id."""

    name: DomainName

    @override
    def kind(self) -> str:
        return "domain_name"

    @override
    def to_dict(self) -> dict[str, Any]:
        return {"name": str(self.name)}


@dataclass
class LookupDomainAction(LookupEntityOpsAction[DomainRow, DomainData]):
    """Resolve a domain's name into the domain it names."""

    name: DomainName

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return DOMAIN_ENTITY_TYPE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "lookup_domain"

    @override
    def lookup_key(self) -> DomainNameKey:
        return DomainNameKey(name=self.name)

    @override
    def to_lookup(self) -> DomainNameLookup:
        return DomainNameLookup(name=self.name)
