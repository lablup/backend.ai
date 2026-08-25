from typing import override

from ai.backend.common.data.entity.types import (
    EntityIdentifier,
    EntityType,
    NaturalKey,
    ScopeType,
)

__all__ = (
    "DOMAIN_ENTITY_TYPE",
    "DOMAIN_SCOPE_TYPE",
    "DomainID",
    "DomainName",
)


# Raw string mirroring the RBAC-managed RBACElementType.DOMAIN value.
DOMAIN_ENTITY_TYPE = EntityType("domain")
DOMAIN_SCOPE_TYPE = ScopeType(DOMAIN_ENTITY_TYPE)


class DomainID(EntityIdentifier):
    @override
    def entity_type(self) -> EntityType:
        return DOMAIN_ENTITY_TYPE


class DomainName(NaturalKey):
    @override
    @classmethod
    def key_name(cls) -> str:
        return "domain_name"
