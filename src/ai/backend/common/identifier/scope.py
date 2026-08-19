from ai.backend.common.identifier.entity import EntityID

__all__ = ("ScopeID",)


# A scope's identifier. Every scope doubles as an entity, so this is an alias of
# EntityID rather than a separate UUID alias: the subset relation is visible in
# the type. The concrete scope kind is discriminated by the accompanying
# scope_type, as the entity kind is by entity_type.
type ScopeID = EntityID
