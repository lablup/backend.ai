"""
Purpose:
    Generate resource entity-type permission rows for fixtures/manager/example-roles.json.

Usage:
    python3 scripts/generate-rbac-fixture-permissions.py

Behavior:
    Treats RESOURCE_ENTITY_TYPES as managed: their rows are stripped from
    permissions[] and re-emitted from each (role x scope) pair found in the
    remaining (base) rows using the canonical session-migration rule:

      - role in EXCLUDED_ROLES                                 -> skip
      - scope_type == 'domain' AND role_name endswith 'member' -> skip
      - role_name endswith 'member'                            -> {READ}
      - else                                                   -> all standard ops

    Idempotent — UUIDv5 IDs and strip-and-re-emit semantics make re-runs
    produce identical output.
"""

from __future__ import annotations

import json
import sys
import uuid
from pathlib import Path

FIXTURE_PATH = (
    Path(__file__).resolve().parent.parent / "fixtures" / "manager" / "example-roles.json"
)

NAMESPACE = uuid.UUID("e6f1f5b7-3a8b-4d3a-9b8e-2f0a4d3e9c10")

MEMBER_ROLE_SUFFIX = "member"

EXCLUDED_ROLES: frozenset[str] = frozenset({
    "role_monitor",
})

OWNER_OPS: tuple[str, ...] = (
    "create",
    "read",
    "update",
    "soft-delete",
    "hard-delete",
)
MEMBER_OPS: tuple[str, ...] = ("read",)

# Bit values mirror ai.backend.common.data.permission.types.Permission (IntFlag).
# Grant operations (grant:*) have no dedicated bit and map to 0 (NONE);
# grant authority remains carried by the legacy `operation` column.
OPERATION_PERMISSION_BIT: dict[str, int] = {
    "read": 1,
    "update": 2,
    "create": 4,
    "soft-delete": 8,
    "hard-delete": 16,
}


def permission_bit(operation: str) -> int:
    return OPERATION_PERMISSION_BIT.get(operation, 0)

RESOURCE_ENTITY_TYPES: tuple[str, ...] = (
    "session",
    "agent",
    "image",
    "keypair",
    "container_registry",
    "resource_group",
    "artifact",
    "artifact_registry",
    "app_config",
    "app_config_fragment",
    "notification_channel",
    "notification_rule",
    "model_deployment",
    "model_card",
)
MANAGED_ENTITY_TYPES: frozenset[str] = frozenset(RESOURCE_ENTITY_TYPES)


def derive_operations(role_name: str, scope_type: str) -> tuple[str, ...]:
    if role_name in EXCLUDED_ROLES:
        return ()
    is_member = role_name.endswith(MEMBER_ROLE_SUFFIX)
    if scope_type == "domain" and is_member:
        return ()
    if is_member:
        return MEMBER_OPS
    return OWNER_OPS


def stable_id(
    role_id: str, scope_type: str, scope_id: str, entity_type: str, operation: str
) -> str:
    key = f"{role_id}|{scope_type}|{scope_id}|{entity_type}|{operation}"
    return str(uuid.uuid5(NAMESPACE, key))


def main() -> int:
    raw = FIXTURE_PATH.read_text(encoding="utf-8")
    data = json.loads(raw)

    roles_by_id = {r["id"]: r for r in data["roles"]}

    base_permissions = [
        p for p in data["permissions"] if p["entity_type"] not in MANAGED_ENTITY_TYPES
    ]
    stripped = len(data["permissions"]) - len(base_permissions)

    # Backfill the bitmask column on pass-through (base) rows so every emitted
    # permission row carries `permission` derived from its `operation`.
    for p in base_permissions:
        p["permission"] = permission_bit(p["operation"])

    role_scopes: set[tuple[str, str, str]] = {
        (p["role_id"], p["scope_type"], p["scope_id"]) for p in base_permissions
    }

    new_rows: list[dict[str, str | int]] = []
    for role_id, scope_type, scope_id in sorted(role_scopes):
        role = roles_by_id.get(role_id)
        if role is None:
            print(f"warning: role {role_id} not found in roles[]; skipping", file=sys.stderr)
            continue
        ops = derive_operations(role["name"], scope_type)
        if not ops:
            continue
        for entity_type in RESOURCE_ENTITY_TYPES:
            for op in ops:
                new_rows.append({
                    "id": stable_id(role_id, scope_type, scope_id, entity_type, op),
                    "role_id": role_id,
                    "scope_type": scope_type,
                    "scope_id": scope_id,
                    "entity_type": entity_type,
                    "operation": op,
                    "permission": permission_bit(op),
                })

    data["permissions"] = base_permissions + new_rows
    FIXTURE_PATH.write_text(json.dumps(data, indent=4) + "\n", encoding="utf-8")

    by_entity: dict[str, int] = {}
    for r in new_rows:
        by_entity[r["entity_type"]] = by_entity.get(r["entity_type"], 0) + 1
    print(
        f"emitted {len(new_rows)} permission rows across {len(by_entity)} entity types"
        f" (stripped {stripped} prior rows):"
    )
    for et in RESOURCE_ENTITY_TYPES:
        if et in by_entity:
            print(f"  {et:24s} {by_entity[et]:4d}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
