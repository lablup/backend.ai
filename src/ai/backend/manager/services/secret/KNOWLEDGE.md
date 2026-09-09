---
name: secret-service
type: design-rationale
description: stored secret operations, global authorization, field data without dedicated rows
scope: src/ai/backend/manager/services/secret
keywords: [SecretFieldType, SecretProcessors, SecretFieldData, SecretStatus, SecretReencryptProgress]
sources:
  - src/ai/backend/manager/services/secret
  - src/ai/backend/manager/actions/registry/field.py
  - src/ai/backend/manager/actions/registry/registry.py
generated:
  by: codex/gpt-6
  at: 2026-09-09
status: draft
---

# Secret operations cover encrypted columns across entities

This package provides status and re-encryption operations over stored secrets across
all encrypted columns, whose owning entity kind is not fixed.

## Both operations require system-wide authorization

- `get_status` and `reencrypt` name no individual row or owner, so both use the global authorization gate.
- The gate permits SUPERADMIN operations and MONITOR reads; other roles are refused.
- Re-encryption returns counts for one pass; its execution remains the repository's responsibility.

## No dedicated secret row is represented

- The field group uses `SecretFieldData`, an empty data type because secrets have no dedicated row; neither operation returns or constructs it.
- Service results carry `SecretStatus` or `SecretReencryptProgress`, independently of the group's row data type.
