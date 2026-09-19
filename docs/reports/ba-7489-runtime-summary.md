# BA-7489 — runtime exercise of every wired v2 action: summary

Three slices, 506 catalog actions, driven against a live local manager as superadmin, domain admin,
plain user and monitor. **Findings only — nothing was fixed.** Each fix group is filed separately.

| slice | concerns | rows | report |
|---|---|---:|---|
| Identity & Access | `organization`, `rbac`, `resource_policy` | 138 | [ba-7489-runtime-identity-access.md](ba-7489-runtime-identity-access.md) |
| Storage & Artifacts | `artifact_registry`, `vfolder`, `container_registry` | 180 | [ba-7489-runtime-storage-artifacts.md](ba-7489-runtime-storage-artifacts.md) |
| Compute & Platform | `resource_group`, `system`, `app_config`, `metric`, `notification_center`, `visibility`, `label` | 188 | [ba-7489-runtime-compute-platform.md](ba-7489-runtime-compute-platform.md) |

`session` and `deployment` were out of scope. Storage & Artifacts carries 180 rows against a 178-action
catalog: the two vfolder bulk adapter loops are scored separately because that is where Q5 bites.

## Conclusion

**53 defects, none of which the static sweep in BA-7486 could have found.** The run answers the five
questions BA-7489 was opened for, and three of the five answers are worse than the wiring suggests.

The single largest result is that **the declared gate is frequently not the gate a request meets**, and
the divergence runs in both directions from one cause: route middleware and the action gate are decided
independently, and nothing reconciles them.

Four live cross-tenant disclosures were found, three of them independently in different slices. Three share
one shape — **v2 takes the owner from a caller-supplied scope field and never constrains it to the caller**;
the fourth drops the scoping filter entirely:

| | |
|---|---|
| `search_app_config_fragments` | any authenticated user reads any other user's user-scope fragments, values included (`api/adapters/app_config_fragment/adapter.py:220`) |
| `get_vfolder_v2` | any domain member reads any other user's vfolder — owner e-mail, name, quota scope |
| `search_users_by_project` / `get_user` | any project member reads every other member's full record, including the superadmin's `main_access_key` |
| `public_list_shared_vfolders` | any authenticated user lists every share in the system — `services/vfolder/services/sharing.py:116` passes `None` to `list_shared_vfolder_permissions`, which removes the filter rather than scoping it. The sibling `list_shared_vfolders` passes a vfolder id |

The last one runs through a different mechanism from `get_vfolder_v2` and needs its own fix: `monitor@` is
*denied* by the domain-member grant that opens the first vfolder leak, yet *served* by this one.

A third pattern appeared twice, again independently: **invitation flows are write-only.** Entity
invitations can be created and cancelled by an administrator and by nobody else — the invitee cannot read,
accept or reject one addressed to them. VFolder invitations are the same: `vfolder_invitation` has zero
rows in `permissions`, so every operation but `invite` returns 403.

Wherever a v1 twin exists, **v2 is the weaker surface**: v1 enforces the ownership check v2 dropped, v1
actually purges where v2 reports a hard delete it does not perform, and the same file operation demands a
different permission depending on which version is called.

## The five questions

| # | question | answer |
|---|---|---|
| Q1 | Is the action reachable from any client at all, and by which route? | **34 have no client route; 11 more are reachable but can never succeed.** 8 of the 34 confirm BA-7486's static verdicts. 5 wired v2 actions are reachable only through v1. |
| Q2 | Is the declared gate the gate the request meets? | **No, on 168 of 506**, in both directions — over-gated where route middleware pre-empts the action gate, under-gated where the RBAC grant is wider than the operation. A further 3 meet the declared gate while the thing that justifies that gate is inert at runtime. |
| Q3 | Does the audit row carry the declared entity_type / operation / action_name? | **Instrumentation is sound; two narrow gaps.** Every mutation and every in-action failure leaves a row. 118 mismatches, mostly the one `global`-kind defect. Route-middleware denials never reach the processor and leave nothing — 109 of 168 actions in one slice alone. |
| Q4 | Are a lookup miss and a permission denial indistinguishable where required? | **No, on 11.** `POST /auth/authorize` distinguishes an unknown user from a wrong password. Three lookup surfaces 404 a miss before any permission check. Error responses additionally return a full server traceback naming the raising function. |
| Q5 | Does a partial bulk answer per named entity, in order, with denials and misses told apart? | **Only where it cannot deny.** See below. |

Counts are the re-scored verdicts from the merged Korean document,
[`v2-action-audit/03-runtime.md`](v2-action-audit/03-runtime.md), which is the authoritative tally.
They are narrower than the per-slice reports' own figures: a `global`/`permission` action denying a
non-admin meets its declared gate by design and is not counted a mismatch, and a leak requires one
caller getting distinguishable answers rather than two callers getting different ones.

### Q5 deserves its own note

Bulk is not one behaviour. Measured across all three slices:

| surface | result |
|---|---|
| GraphQL DataLoader batches (4 measured, 2 slices) | correct — one answer per input, in order, duplicates independent, misses at their own position |
| `vfolder bulk-delete` | collapses to one 403 **and still soft-deletes the permitted item**; order-dependent |
| `vfolder bulk-purge` | `{purged_count, failed[]}` with no positional mapping; double-counts duplicates |
| `delete_artifacts` | returns `{"artifacts": []}` and an audit success for ids that do not exist |
| `global_create_users` | aborts the whole batch when one item names a missing domain |
| `global_purge_users` | reports successes only as a count |
| `assign_users_to_project` | drops unknown users silently, aborts on a duplicate |

The DataLoader pass must not be over-read. **All four correct loaders are gated `public`, so no denied item
can be constructed on them** — a miss is the only negative outcome available. Every bulk surface in the
audit that *can* deny is a surface that fails Q5. The clause "denials and misses told apart" is therefore
effectively unverified, not verified.

## Cross-slice defects

Found independently in more than one slice. Each is one fix, not three.

| defect | where |
|---|---|
| Every `global`-kind action records `entity_type = 'global'` instead of the declared type — `actions/v2/global_scope/monitor/audit_log.py:73` passes `GLOBAL_ENTITY_TYPE` rather than `action.entity_type()` | all three |
| Every RBAC denial reports `role_create_forbidden` — `errors/permission.py:93` hardcodes `ErrorDomain.ROLE` + `ErrorOperation.CREATE` regardless of entity and operation | all three |
| Route-level `superadmin_required` denials never reach the action processor, so nothing is audited, though `AuditLogPolicy` states that anything denied is always recorded | all three |
| Error responses carry the full server traceback to the client. Worse on entity create: `_match_integrity_error` (`repositories/ops/v2/write_base.py:233`) re-raises the parsed integrity error whenever no declared check matches the violated constraint, and that error carries the SQLAlchemy statement **with its bound parameters** — so a v2 create that trips an undeclared unique constraint returns its own inputs, `secret_key` in cleartext included. Measured on `POST /v2/object-storages` (16,633-byte 409 body) and reproduced on `reservoir-registry create`. Any secret-bearing create is affected | Identity & Access, Storage |
| The whole audit-log read surface is unusable from every client: `client_ip` is `inet` in the DB but `str \| None` in the DTO, breaking `GET /v2/audit-logs`, `adminAuditLogsV2` and `scopedAuditLogsV2` alike | found at lead level, confirmed in two slices |

## Severity-ranked findings

Ranked across all three reports. The per-slice reports carry the reproduction for each.

| # | finding | slice |
|---|---|---|
| 1 | Any project member reads every other member's record including the superadmin's access key | Identity |
| 2 | Any authenticated user reads any other user's app-config fragments, values included | Platform |
| 3 | Any domain member reads any other user's vfolder | Storage |
| 4 | Harbor webhook authenticates nobody on a default deployment and makes the manager fetch a caller-supplied URL | Storage |
| 4= | `public_list_shared_vfolders` lists every share in the system to any authenticated caller | Storage |
| 5 | `cancel_import` is an unguarded status reset — undoes a rejection, strands imported files with no API path to download or reclaim them | Storage |
| 6 | `purge_vfolder_v2` reports a hard delete it does not perform (`purge_v2` calls `delete_vfolders_forever`; the real `purge_vfolder` sits unused beside it) | Storage |
| 7 | `POST /auth/authorize` distinguishes an unknown user from a wrong password | Identity |
| 8 | Entity-invitation flow cannot be completed by any principal | Identity |
| 9 | VFolder invitations are write-only for every non-superadmin | Storage |
| 10 | `scan_artifacts` cannot use any registry created through the API — registry identity is DB-backed in the manager and file-backed in the proxy, with nothing reconciling them | Storage |
| 11 | Projects created through the API get no RBAC roles, so nobody can ever be granted access | Identity |
| 12 | Audit rows record `success` for runs that failed — including a 500 whose row reads `Success` | Identity |
| 13 | A user cannot read their own projects, their own resource policy, or their own app-config | Identity, Platform |
| 14 | `GET /resource/presets` always 500s — `normalize_slots()` reads a ContextVar that only the setting request can see | Platform |
| 15 | Bulk runs give no per-item answer, and one silently writes orphan rows for a nonexistent domain | Platform |

Remaining findings are in the per-slice reports: 19 in Identity & Access, 17 in Storage & Artifacts,
17 in Compute & Platform.

## What this run could not test

| gap | reason |
|---|---|
| 15 Storage actions | no Harbor, no live compute agent, no delegatee reservoir |
| 3 agent lifecycle actions | no live compute agent or watcher; running them would have destabilised the shared stack |
| 7 Platform actions | reachable only from an internal caller, no client-facing field |
| Q5 denial clause | no bulk surface that both denies and behaves correctly exists to compare against |

`agent`, `proxy-coordinator` and `proxy-worker` were stopped for the whole run; the `agents` table held
one `TERMINATED` row.

## Environment repairs, explicitly not findings

The local stack was partly down and partly misconfigured at the start. All of this was dev-config drift,
was repaired at lead level mid-run, and **every affected row was re-run afterwards**. None of it is
reported as a defect anywhere.

| repair | detail |
|---|---|
| storage-proxy started | `./dev status` reported it stopped |
| MinIO started | container was not running |
| manager/proxy shared secret aligned | `storage-proxy.toml` had `510def4b…`, etcd `volumes/proxies/local/secret` had `8887e958…`; manager restarted to clear its cached view |
| `backendai-storage` bucket created | did not exist |
| proxy MinIO credentials repointed | the configured access key did not exist in the instance |
| migration `f4b1c9d27a08` applied | DB sat one revision behind head, so `entity_invitations` was absent |

Three unprefixed rows were deliberately left in place because the deployment's own config names them and
the artifact chain does not work without them: the `huggingface-hub` registry, the `minio-storage` object
storage, and its `backendai-storage` namespace. All `ba7489a-` / `ba7489b-` / `ba7489c-` test entities
were removed.

## Method notes

Three agents ran concurrently against one manager, isolated by API-mode HMAC credentials passed per
command rather than the shared session cookie. Audit rows were read by direct SQL because the audit-log
API is broken (see cross-slice defects).

Two measurement errors were made and corrected during the run, both in the same direction: a batch of
mutations was labelled `no row` without being probed, and a marker helper mangled its timestamp. Both
produced false `no row` labels and both were re-measured against the table. **The corrected picture is the
opposite of the first draft** — audit instrumentation is broadly sound, and the two real gaps are narrow
and specific. A reader who sees only the early figures would draw the wrong conclusion about the system.
