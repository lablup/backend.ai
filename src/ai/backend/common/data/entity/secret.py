from ai.backend.common.data.entity.types import EntityType

__all__ = ("SECRET_ENTITY_TYPE",)


# The stored secrets of every encrypted column. Named on its own rather than under one
# of the entities holding them: the same operation covers all of those columns.
SECRET_ENTITY_TYPE = EntityType("secret")
