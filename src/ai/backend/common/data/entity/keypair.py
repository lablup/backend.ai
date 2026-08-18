from ai.backend.common.data.entity.types import EntityType

__all__ = ("KEYPAIR_ENTITY_TYPE",)


# Raw string mirroring the RBAC-managed EntityType.KEYPAIR value. A keypair is a field of
# its user; the type names what the row is, not something the graph holds a node for.
KEYPAIR_ENTITY_TYPE = EntityType("keypair")
