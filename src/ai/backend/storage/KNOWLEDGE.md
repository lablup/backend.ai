---
name: storage-proxy-trust-split
type: design-rationale
description: The storage proxy as a stateless data plane, the trust split between client JWTs and the manager shared secret, absence of a relational database, the quota-scope model with per-backend capabilities, the privileged watcher subprocess, TUS upload leases in Valkey
scope: src/ai/backend/storage
keywords: [storage-proxy, JWT, quota-scope, AbstractVolume, CAP_QUOTA, TUS, watcher, stateless]
sources:
  - src/ai/backend/storage/api
  - src/ai/backend/storage/volumes/abc.py
generated:
  by: claude-code/fable-5
  at: 2026-08-10
status: stable
---

# Storage Proxy — Knowledge

> Rules: `AGENTS.md` in the same directory.

## Why this component exists

It is the stateless data plane between Backend.AI and the actual
filesystems/object stores — it handles file upload/download/streaming and the
vfolder/quota lifecycle, and confines vendor specifics behind a single volume
interface.

## Two APIs, two trust models

- The client-facing API (untrusted network) authenticates nothing itself — every request carries a short-lived JWT **issued by the manager**, whose payload spells out volume/vfolder/path/size.
- Authorization was already decided at issuance time; the proxy only verifies the signature.
- The manager-facing API (trusted network) uses a shared-secret header.
- Therefore adding a client endpoint means **adding a token type plus a manager-side issuer**, not adding a permission check.

## It is stateless by construction

- There is no relational DB — persistent metadata lives in the manager's DB, and the proxy uses only etcd (configuration) and Valkey (events, background tasks, TUS offsets, volume statistics).
- Managing TUS offsets via Valkey leases exists so that multiple proxy replicas can serve the same upload session.
- Do not add tables — persistent state belongs in the manager.

## The quota unit is a quota scope, not a folder

- The quota unit is a quota scope (`(type, uuid)` — user or project), and vfolder paths are derived under that scope.
- Quota support is a **per-backend capability** (`CAP_QUOTA`), not a guarantee — code must branch and tolerate its absence.

## Vendor specifics stay behind the volume interface

- Every vendor sits behind `AbstractVolume` + `AbstractQuotaModel` + `AbstractFSOpModel`.
- Backends may mutate host state (XFS edits `/etc/projects` via sudo).
- Operations that need root in the proxy itself go through the opt-in watcher subprocess (ZeroMQ IPC, task objects) — no inline sudo inside handlers.
