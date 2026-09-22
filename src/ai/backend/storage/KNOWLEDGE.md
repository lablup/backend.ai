---
name: storage-proxy-trust-split
type: design-rationale
description: The storage proxy as a stateless data plane, the trust split between client JWTs and the manager shared secret, absence of a relational database, the quota-scope model with per-backend capabilities, the privileged watcher subprocess, TUS upload leases in Valkey, the composed startup dependency stages
scope: src/ai/backend/storage
keywords: [storage-proxy, JWT, quota-scope, AbstractVolume, CAP_QUOTA, TUS, watcher, stateless, StorageDependencyComposer, StoragePluginContext, VolumePool]
sources:
  - src/ai/backend/storage/api
  - src/ai/backend/storage/volumes/abc.py
  - src/ai/backend/storage/dependencies
generated:
  by: claude-code/opus-5
  at: 2026-09-10
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

## Startup is one composed dependency graph

- `StorageDependencyComposer` owns every startup resource, and the server,
  `dependencies verify` and `health check` all drive it — a resource assembled
  by hand in one path is invisible to the others.
- Plugin contexts are composed once and injected: the volume registry receives
  the backend classes it needs instead of loading the plugin group itself.
- `RootContext` is assembled in `server.py` from the composed resources — it is
  a carrier, not a stage.

## `VolumePool` is the only volume registry

- Every configured volume is constructed and `init()`ed once by
  `VolumePool.create()`, which also registers the noop volume, and is addressed
  by its `[volume.<name>]` configuration key; nothing builds a volume on a
  request path.
- A UUID configuration key is canonicalised, so `get_volume(VolumeID)` and
  `get_volume_by_name(key)` reach the same object.
- Because initialisation is eager, a volume whose mount is broken fails the
  whole startup instead of failing on its first request.
