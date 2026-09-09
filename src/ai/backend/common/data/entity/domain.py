from typing import override

from ai.backend.common.data.entity.types import (
    EntityIdentifier,
    EntityType,
    NaturalKey,
    ScopeType,
)

__all__ = (
    "DomainEntityType",
    "DOMAIN_SCOPE_TYPE",
    "DomainID",
    "DomainName",
)


class DomainEntityType(EntityType):
    @override
    @classmethod
    def name(cls) -> str:
        return "domain"

    @override
    @classmethod
    def description(cls) -> str:
        return "The top-level tenant holding projects and users."


DOMAIN_SCOPE_TYPE = ScopeType(DomainEntityType())


class DomainID(EntityIdentifier):
    @override
    def entity_type(self) -> EntityType:
        return DomainEntityType()


class DomainName(NaturalKey):
    @override
    @classmethod
    def key_name(cls) -> str:
        return "domain_name"
