from __future__ import annotations

from ai.backend.manager.actions.types import ActionSpec

# Actions to exclude from audit logging
# These are high-frequency actions that would create excessive log entries
AUDIT_LOG_EXCLUDED_ACTIONS: frozenset[ActionSpec] = frozenset({
    ActionSpec(entity_type="agent", operation_type="handle_heartbeat"),
})
