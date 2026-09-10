"""Entity type and id of the entity memberships table."""

from typing import override

from ai.backend.common.data.entity.types import EntityIdentifier, EntityType

__all__ = ("EntityMembershipEntityType", "EntityMembershipID")


class EntityMembershipEntityType(EntityType):
    @override
    @classmethod
    def name(cls) -> str:
        return "entity_membership"

    @override
    @classmethod
    def description(cls) -> str:
        return "One entity held by another's virtual entity, either owned outright or lent."


class EntityMembershipID(EntityIdentifier):
    """A membership edge's entity id.

    The edge is an entity of its own rather than a field of either end: it names two
    virtual entity nodes and belongs to neither, and its cap rows hang off it.
    """

    @override
    def entity_type(self) -> EntityType:
        return EntityMembershipEntityType()
