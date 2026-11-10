"""
The singleton rows and their graph nodes.

Executed by the migration and by `mgr schema oneshot`, which builds a fresh database
without running migrations. One statement per string.
"""

SEED_GLOBAL_ENTITIES_SQL: tuple[str, ...] = (
    """
    INSERT INTO global_entities (name) VALUES ('global'), ('public')
    ON CONFLICT (name) DO NOTHING
    """,
    """
    INSERT INTO virtual_entities (entity_type, entity_id)
    SELECT 'global', id FROM global_entities
    ON CONFLICT (entity_type, entity_id) DO NOTHING
    """,
    """
    INSERT INTO entity_memberships (virtual_entity_id, member_entity_id, capped)
    SELECT id, id, FALSE FROM virtual_entities WHERE entity_type = 'global'
    ON CONFLICT (virtual_entity_id, member_entity_id) DO NOTHING
    """,
    """
    INSERT INTO scope_bindings (virtual_entity_id, scope_entity_id, permission_cap)
    SELECT id, id, NULL FROM virtual_entities WHERE entity_type = 'global'
    ON CONFLICT DO NOTHING
    """,
)
