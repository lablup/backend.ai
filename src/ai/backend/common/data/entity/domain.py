from typing import override

from ai.backend.common.data.entity.types import EntityIdentifier, EntityType, NaturalKey

__all__ = (
    "DomainEntityType",
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


class DomainID(EntityIdentifier):
    @override
    def entity_type(self) -> EntityType:
        return DomainEntityType()


class DomainName(NaturalKey):
    @override
    @classmethod
    def key_name(cls) -> str:
        return "domain_name"
