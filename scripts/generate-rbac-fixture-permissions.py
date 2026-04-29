"""
Purpose:
    Generate resource entity-type permission rows for fixtures/manager/example-roles.json.

Usage:
    python3 scripts/generate-rbac-fixture-permissions.py

Behavior:
    For each (role x scope) pair already in permissions[], emit rows for every
    resource entity-type using the canonical session-migration rule:

      - role in EXCLUDED_ROLES                                 -> skip
      - scope_type == 'domain' AND role_name endswith 'member' -> skip
      - role_name endswith 'member'                            -> {READ}
      - else                                                   -> all owner ops

    Idempotent — UUIDv5 IDs make re-runs produce identical output.
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
    "role_superadmin",
    "role_monitor",
})

OWNER_OPS: tuple[str, ...] = (
    "create",
    "read",
    "update",
    "soft-delete",
    "hard-delete",
    "grant:all",
    "grant:read",
    "grant:update",
    "grant:soft-delete",
    "grant:hard-delete",
)
MEMBER_OPS: tuple[str, ...] = ("read",)

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
    "notification_channel",
    "notification_rule",
    "model_deployment",
    "model_card",
)


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
    permissions = data["permissions"]

    existing_keys = {
        (p["role_id"], p["scope_type"], p["scope_id"], p["entity_type"], p["operation"])
        for p in permissions
    }

    role_scopes: set[tuple[str, str, str]] = {
        (p["role_id"], p["scope_type"], p["scope_id"]) for p in permissions
    }

    new_rows: list[dict[str, str]] = []
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
                key = (role_id, scope_type, scope_id, entity_type, op)
                if key in existing_keys:
                    continue
                new_rows.append({
                    "id": stable_id(role_id, scope_type, scope_id, entity_type, op),
                    "role_id": role_id,
                    "scope_type": scope_type,
                    "scope_id": scope_id,
                    "entity_type": entity_type,
                    "operation": op,
                })

    if not new_rows:
        print("no new permission rows; fixture is already up to date")
        return 0

    data["permissions"] = permissions + new_rows
    FIXTURE_PATH.write_text(json.dumps(data, indent=4) + "\n", encoding="utf-8")

    by_entity: dict[str, int] = {}
    for r in new_rows:
        by_entity[r["entity_type"]] = by_entity.get(r["entity_type"], 0) + 1
    print(f"added {len(new_rows)} permission rows across {len(by_entity)} entity types:")
    for et in RESOURCE_ENTITY_TYPES:
        if et in by_entity:
            print(f"  {et:24s} {by_entity[et]:4d}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
