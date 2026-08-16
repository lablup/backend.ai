import uuid
from typing import NewType

from ai.backend.common.data.entity.types import EntityType, ScopeType

__all__ = (
    "DOMAIN_ENTITY_TYPE",
    "DOMAIN_SCOPE_TYPE",
    "DomainID",
    "DomainName",
)


# Raw string mirroring the RBAC-managed RBACElementType.DOMAIN value.
DOMAIN_ENTITY_TYPE = EntityType("domain")
DOMAIN_SCOPE_TYPE = ScopeType(DOMAIN_ENTITY_TYPE)

DomainID = NewType("DomainID", uuid.UUID)
DomainName = NewType("DomainName", str)
