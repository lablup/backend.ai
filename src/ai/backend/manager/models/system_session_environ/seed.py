"""
Every value source bound at the global scope under the name the launcher has always used.

Executed by the migration and by `mgr schema oneshot`, after the global entities.
"""

SEED_SYSTEM_SESSION_ENVIRON_SQL: tuple[str, ...] = (
    """
    INSERT INTO system_session_environ (value_source, key, scope_type, scope_id, enabled)
    SELECT binding.value_source, binding.key, 'global', global_entities.id, binding.enabled
    FROM (
        VALUES
            ('session_id', 'BACKENDAI_SESSION_ID', TRUE),
            ('session_name', 'BACKENDAI_SESSION_NAME', TRUE),
            ('cluster_size', 'BACKENDAI_CLUSTER_SIZE', TRUE),
            ('cluster_replicas', 'BACKENDAI_CLUSTER_REPLICAS', TRUE),
            ('cluster_hosts', 'BACKENDAI_CLUSTER_HOSTS', TRUE),
            ('preopen_ports', 'BACKENDAI_PREOPEN_PORTS', TRUE),
            ('user_uuid', 'BACKENDAI_USER_UUID', FALSE),
            ('user_email', 'BACKENDAI_USER_EMAIL', FALSE),
            ('user_name', 'BACKENDAI_USER_NAME', FALSE),
            ('access_key', 'BACKENDAI_ACCESS_KEY', FALSE)
    ) AS binding (value_source, key, enabled)
    CROSS JOIN global_entities
    WHERE global_entities.name = 'global'
    ON CONFLICT (key, scope_type, scope_id) DO NOTHING
    """,
)
