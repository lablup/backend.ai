# BA-7489 runtime test — Storage & Artifacts

Runtime exercise of the wired v2 actions in the `artifact_registry`, `vfolder` and `container_registry`
concerns against the live local manager. Findings only — nothing was fixed.

| | |
|---|---|
| Jira | BA-7489 |
| Slice | storage-artifacts (agent B) |
| Catalog rows | 178 (`artifact_registry` 71, `vfolder` 68, `container_registry` 39) |
| Manager | `http://127.0.0.1:8091`, direct API mode (HMAC) |
| Entity prefix | `ba7489b-` — all fixtures created and removed again |

## Conclusion

Seventeen defects, none of which the static sweep could have found. Five matter most:

| | |
|---|---|
| **F1** | `get_vfolder_v2` lets any domain member read any other user's vfolder — the v1 route still enforces the ownership check that v2 dropped |
| **F2** | `cancel_import` is an unguarded status reset: it undoes a rejection, and on an imported revision it strands the files in object storage with no API path left to download or reclaim them |
| **F3** | `scan_artifacts` cannot use any registry created through the API — the storage proxy resolves registries by name against its own TOML |
| **F4** | the Harbor webhook authenticates nobody on a default deployment and makes the manager fetch a caller-supplied URL |
| **F5** | `purge_vfolder_v2` reports a hard delete it does not perform; the row survives while the v1 purge of the same folder removes it |

Two themes run underneath. **The v2 surface is the weaker one wherever a v1 twin exists**: v1 enforces the
ownership check (F1), v1 actually purges (F5), and the same file operation demands a different permission
depending on which version you call (F10). And **bulk is not one behaviour** — the three bulk-shaped surfaces
here answer three different ways (F9), with only the GraphQL DataLoader path satisfying Q5.

Two of the reads leak through different mechanisms and need separate fixes: F1 is a domain-scope grant wider
than the operation, F17 is a `public` endpoint that never scopes its result. `monitor@` is denied by the first
and served by the second.

Audit instrumentation is sounder than it first looked: measured against `AuditLogPolicy`, every mutation and
every in-action failure leaves a row. The two real gaps are route-middleware denials, which never reach the
processor (F12), and a legacy GraphQL mutation that bypasses it (F16.4). Agent A's finding that every
`global`-kind action records `entity_type='global'` is visible across most of my registry and storage rows.

### Coverage

| | count |
|---|---:|
| exercised (admin and, where gated, non-admin) | 145 |
| reachable but blocked on an absent backend (Harbor / compute agent / delegatee reservoir) | 15 |
| unreachable — no caller, or the processor is bypassed | 15 |
| internal-only lookups with no client route | 5 |
| **total** | **180** |

The `artifact` and `artifact_revision` actions moved into "exercised" after the environment was repaired
mid-run: the chain was driven end to end — scan two models from HuggingFace Hub, import one into MinIO
(9 objects), read it back through a presigned URL, then clean it up (bucket back to 0).

180 rows against a 178-row catalog: `vfolder bulk-delete` and `vfolder bulk-purge` are listed separately
because they are adapter-level loops over `delete_vfolder_v2` / `purge_vfolder_v2` rather than catalog rows
of their own, and they are where Q5 actually bites.

### Environment caveats

The storage proxy and MinIO were down for the first part of this run and were repaired mid-run at lead level
(storage-proxy started, MinIO started, a manager/proxy shared-secret mismatch corrected, the
`backendai-storage` bucket created, and the proxy's MinIO credentials repointed). That was local dev-config
drift, not action wiring: **every row affected by it was re-run afterwards and none of it is reported as a
finding here.** The artifact scan and import chain was subsequently driven end to end against the real
HuggingFace Hub, so the `artifact` and `artifact_revision` rows below reflect real scanned and imported data.

Still absent, and scoped accordingly:

- **No compute agent** (`agents` holds one TERMINATED row), so `get_image_installed_agents` returns empty and
  `get_task_logs` has no session log to read.
- **No Harbor instance**, so `untag_image_from_registry` and the four registry-quota actions cannot complete.
- **No second reservoir**, so the two `delegate_*` actions have no delegatee.

**State left behind.** All `ba7489b-` fixtures were removed, the seeded image I forgot during F8 was restored
by rescan (154 ALIVE / 0 DELETED), the global mount created during testing was unmounted, and the MinIO bucket
is back to 0 objects. Three rows are deliberately left in place because the deployment's own config names
them and the artifact chain does not work without them: the `huggingface-hub` artifact registry, the
`minio-storage` object storage, and its `backendai-storage` namespace. They carry no `ba7489b-` prefix for
that reason.

### How the gates actually resolve

Worth stating once, because it explains most of the `Q2 mismatch` verdicts below. Every REST v2 route for
`vfs_storage`, `object_storage`, `storage_namespace`, `artifact`, `huggingface_registry`,
`reservoir_registry`, `container_registry` and `image` carries `superadmin_required` **route middleware**.
Every RBAC validator returns early for a superadmin. So for the `single_entity/permission` actions on those
routes the per-entity RBAC check the catalog advertises can neither grant nor deny — it is unreachable in
both directions, and the effective gate is a hardcoded superadmin check at `auth.py:917`.

`vfolder` is the exception: its routes carry `auth_required`, the RBAC validator really runs, and that is why
every genuine permission finding in this slice is a vfolder finding.

### How the audit rows were scored, and a correction

`AuditLogPolicy` records every mutation and every failure always, and a successful read only when that
operation is opted in — and none is opted in here. Measured against that rule **the instrumentation is
broadly sound**: every mutation and every in-action failure driven in this slice left a row. `no row
(successful read)` below is the policy working, not a defect, and the only genuine audit gaps are two narrow
and specific ones — route-middleware denials (F12) and one legacy GraphQL mutation that bypasses the
processor (F16.4).

That is the opposite of what an earlier draft of this report said, and the reason is worth recording. My first
pass used a shell helper that captured `max(created_at)` as a marker and stripped whitespace from it, which
turned `2026-08-25 15:27:32+00` into an invalid timestamp literal; the follow-up query then silently returned
nothing. Roughly twenty actions were scored `no row` on that basis. Re-measured one at a time against a fixed
marker, every one of them — `global_mount_host`, `global_umount_host`,
`update_invited_vfolder_mount_permission`, `share_vfolder`, `unshare_vfolder`, `move_vfolder_file`,
`rename_vfolder_file`, `update_vfolder_quota`, `restore_image_by_id` and the rest — does leave a row. Those
cells now read `match`.

The conclusion a reader would have drawn from the first draft ("the audit surface is far narrower than the
catalog implies") was an artifact of the measurement, not a property of the system. The two gaps that survive
scrutiny are real, and they are the ones named above.

---

## Findings

Ranked most severe first. F1-F3 and F5 are new; the rest were also visible statically but are confirmed here
with a live reproduction.

### F1 — `get_vfolder_v2` lets any domain member read any other user's vfolder

| | |
|---|---|
| Declared | `vfolder` / `get` / `get_vfolder_v2`, `single_entity` / `permission` |
| Actual | Any user holding the seeded domain member role reads any vfolder in the domain by UUID |
| Blast radius | Every vfolder in a domain, for every ordinary user — owner e-mail, folder name, quota scope id, creator |

`role_domain_default_member` grants `vfolder read` at **domain** scope. `get_vfolder_v2` checks that grant and
nothing else, so ownership never enters the decision.

```bash
# user2@ reads a folder owned by user@ -> 200
BACKEND_ACCESS_KEY=AKIANATWOUSEREXAMPLE BACKEND_SECRET_KEY='P7oxTDdzHbEpUSs5v7r7EWj9yKstp8VpZ7SEyA-g' \
  ./bai vfolder get 196663ce-dbaa-490a-9844-8e324bbae432
# -> {"id": "...", "ownership": {"creator_email": "user@lablup.com", ...}}
```

Three things make this a regression rather than a policy choice:

- the **v1** route for the same entity refuses it — `GET /folders/{id}` returns 404 to user2@ *and* to the
  superadmin, because `_vfolder_resolver` scopes the lookup by ownership;
- `GET /folders/{id}/files` also returns 404 to user2@, so the folder's *contents* stay protected while its
  metadata does not;
- every other single-entity vfolder action (`delete`, `purge`, `mkdir`, `rm`, `mv`, `clone`, `rename`) denies
  user2@ correctly with 403. Only `get` is open.

`monitor@` is denied, which confirms the mechanism: monitor is not a member of the domain member role.

Successful reads are not audited, so these accesses leave no trace.

### F2 — `cancel_import` is an unguarded status reset that strands files in object storage

| | |
|---|---|
| Declared | `artifact_revision` / `update` / `cancel_import` — cancel an in-progress import |
| Actual | Unconditional `UPDATE ... SET status = SCANNED` from **any** status, with no check that an import is running and no effect on stored bytes |
| Blast radius | Reverses a reviewer's rejection; strands imported files in object storage with no API-reachable way to download or reclaim them |

`reset_artifact_revision_status` (`repositories/artifact/db_source/db_source.py:228`) has no status guard at
all. Two transitions that should be impossible:

```bash
./bai artifact revision reject <rev>          # status -> REJECTED
./bai artifact revision cancel-import <rev>   # status -> SCANNED   (moderation decision silently undone)
```

The storage case is worse. Starting from a fully imported revision:

```bash
# revision AVAILABLE, 9 objects (~3.8 MB) in the backendai-storage bucket
./bai artifact revision cancel-import 2711955f-a709-4beb-8ad2-f934229ce463
# -> 200, status becomes SCANNED. The 9 objects are untouched.
```

The bytes are now unreachable and unreclaimable through the API:

| attempt | result |
|---|---|
| `getPresignedDownloadUrl` | 403 `artifact_access_forbidden` — "Only available artifacts can be downloaded" |
| `./bai artifact revision cleanup` | 400 `artifact_purge_bad-request` — "status not ready to be deleted" |
| direct S3 listing | the 9 objects are still there |

`cleanup_artifact_revision` is the only reclamation path and it requires `AVAILABLE`, which `cancel_import`
has just taken away. Verified by re-importing and running cleanup on `AVAILABLE`, which does empty the bucket
(9 objects -> 0) — so the cleanup path itself is sound; `cancel_import` is what breaks the invariant.

### F3 — `scan_artifacts` cannot use any registry created through the API

| | |
|---|---|
| Declared | `artifact` / `create` / `scan_artifacts`, `global` / `permission` |
| Actual | The storage proxy resolves the registry **by name against its own static TOML**, so any registry created via `create_hugging_face_registry` fails with an opaque 404 |
| Blast radius | The supported way to add an artifact registry produces a registry that cannot be scanned. Only names hardcoded in `storage-proxy.toml` work |

```bash
./bai huggingface-registry create --name ba7489b-hf1 --url https://huggingface.co   # -> 200
# then scan with that registry id
# -> "Unexpected response from storage proxy. (Unexpected error 404 from storage proxy)"
```

The manager passes the DB row's `name` through to the proxy, and
`storage/services/artifacts/huggingface.py:354` looks it up in `self._registry_configs` — populated from
`[artifact-registries.*]` in the proxy's TOML — raising `RegistryNotFoundError` when absent. Creating a DB row
named `huggingface-hub` (the one name the TOML declares) makes the identical call succeed and return two
artifacts, which isolates the cause to the name coupling and nothing else.

Registry identity is DB-backed in the manager and file-backed in the proxy, and nothing reconciles them. The
404 surfaced to the client names neither the registry nor the reason.

### F4 — the Harbor webhook authenticates nobody and fetches a caller-supplied URL

| | |
|---|---|
| Declared | `container_registry` / `update` / `handle_harbor_webhook`, `global` / `anonymous` |
| Actual | Unauthenticated. On every registry in this deployment, including the three seeded `cr.backend.ai` rows, the secret check is skipped entirely |
| Blast radius | Anyone who can reach the manager port can make it perform outbound requests to a host they name, and trigger a registry rescan |

`service.py:213` only compares a secret when the registry row carries `extra["webhook_auth_header"]`. All four
registries in this database have `extra` null, so the branch never runs.

```bash
curl -X POST http://127.0.0.1:8091/container-registries/webhook/harbor \
  -H 'Content-Type: application/json' \
  -d '{"type":"PUSH_ARTIFACT","event_data":{"repository":{"namespace":"ba7489b","name":"testimg"},
       "resources":[{"resource_url":"ba7489b.example.com/ba7489b/testimg:latest","tag":"latest"}]}}'
# -> 500, and the traceback shows the manager resolving DNS for ba7489b.example.com
```

No credentials, no signature, no session. The 500 is the point: the request passed routing, matched a registry
row, passed the absent auth check, and reached `scanner.scan_single_ref`, which made the manager contact the
host named in `resource_url`. BA-7486 recorded this as `G` ("the justification is conditional"); at runtime the
condition is false everywhere by default.

I did not fire this against `cr.backend.ai` — proving the bypass on my own registry row was enough, and the
real registries belong to a third party.

### F5 — `purge_vfolder_v2` reports a hard delete it does not perform

| | |
|---|---|
| Declared | `vfolder` / `purge` / `purge_vfolder_v2`, HARD_DELETE. The repository's own purge is documented "Permanently delete a VFolder from DB" |
| Actual | Returns 200 with the id echoed and audits `purge \| success`, but the row survives at `delete-complete` |
| Blast radius | Purge is the tenant-facing "remove it for good" operation. Callers are told the row is gone when it is not |

Two implementations exist and the v2 action uses the wrong one:

| action | route | repository call | row after |
|---|---|---|---|
| `purge_vfolder` (v1) | `POST /folders/purge` | `purge_vfolder` -> `purge_entity` | **gone** |
| `purge_vfolder_v2` | `POST /v2/vfolders/{id}/purge`, `./bai vfolder purge` | `delete_vfolders_forever` | **survives** at `delete-complete` |

Isolated on one folder, same declared operation:

```bash
./bai vfolder delete 0e07a8e7-a149-4e8c-bbbc-87b26e00e20e
./bai vfolder purge  0e07a8e7-a149-4e8c-bbbc-87b26e00e20e
# -> 200; audit purge_vfolder_v2|vfolder|purge|success; SELECT still returns the row, status=delete-complete

# same folder, v1 route, as superadmin
POST /folders/purge {"vfolder_id":"0e07a8e7-..."}
# -> 204; audit purge_vfolder|vfolder|purge|success; SELECT returns 0 rows
```

`purge_v2` (`services/vfolder/services/vfolder.py:1870`) calls `delete_vfolders_forever`, which is what
`delete_forever_vfolder` is for. The two routes also differ in gate: v1 purge is superadmin-only
(`handler.py:1503`, "You are not allowed to purge vfolders") while v2 purge is open to the owner.

### F6 — the vfolder invitation workflow is write-only for every non-superadmin

| | |
|---|---|
| Declared | 9 `vfolder_invitation` actions, `permission`-gated |
| Actual | `invite_vfolder` succeeds; the other eight deny every non-superadmin |
| Blast radius | Sharing a vfolder by invitation does not work for ordinary users at all |

`vfolder_invitation` has **zero** rows in the `permissions` table:

```sql
select count(*) from permissions where entity_type like '%invitation%';  -- 0
```

`invite_vfolder` is gated on the *vfolder*, which the inviter owns, so it returns 201. Everything downstream is
gated on `vfolder_invitation`, which nobody holds any permission on:

```bash
# user@ creates an invitation for user2@ -> 201
POST /folders/196663ce-.../invite   {"perm":"rw","emails":["user2@lablup.com"]}

# user@ cannot see it
GET  /folders/invitations/list-sent
# 403 role_create_forbidden — lacks READ on vfolder_invitation at
#     ScopeRef(scope_type='user', scope_id=<user@'s own id>)

# user2@ cannot see, accept, or reject the invitation addressed to them
GET  /folders/invitations/list      -> 403
POST /folders/invitations/accept    -> 403 (lacks UPDATE on vfolder_invitation)
POST /folders/invitations/delete    -> 403
```

A user is denied READ **at their own user scope**. Combined with F7 this is the real damage: with invitations
dead and sharing admin-only, an ordinary user has no working way to share a folder by any route.

### F7 — `share_vfolder` / `unshare_vfolder` are admin-only despite a per-entity permission gate

| | |
|---|---|
| Declared | `vfolder` / `update` / `share_vfolder`, `single_entity` / `permission` |
| Actual | Route carries `admin_required` (`auth.py:887`); the folder's own owner gets 403 |
| Blast radius | Owners cannot share their own folders. With F6, no sharing path works for ordinary users |

```bash
# user@ sharing a folder user@ owns
POST /folders/30d5b368-.../share  {"permission":"ro","emails":["user2@lablup.com"]}
# -> 403 backendai_generic_forbidden @ auth.py:887  (route middleware, before any RBAC check)

# and as superadmin the operation is restricted further, to project folders only
# -> 404 "Only project folders are directly sharable."
```

`change_vfolder_ownership` has the same shape — `superadmin_required` on the route, `single_entity/permission`
in the catalog.

### F8 — `restore_image_by_id` can never restore a forgotten image

| | |
|---|---|
| Declared | `image` / `restore` / `restore_image_by_id`, `single_entity` / `permission` |
| Actual | 404 `image_read_not-found` for exactly the images the endpoint exists to restore |
| Blast radius | `forget_image` is irreversible through the API. Recovery needs a full registry rescan |

`mark_image_alive_by_id` calls `_get_image_by_id` with no status filter, and `ImageRow.get` defaults
`filter_by_statuses` to `[ImageStatus.ALIVE]` (`models/image/row.py:298`). A `DELETED` row is never found.

```bash
./bai admin image forget 02dab87a-6a9d-4c8f-add0-41eb27421d09     # -> ok, status becomes DELETED
POST /v2/images/restore {"image_id":"02dab87a-6a9d-4c8f-add0-41eb27421d09"}
# -> 404 image_read_not-found
```

I hit this on a seeded image and recovered it with
`mutation { rescan_images(registry:"cr.backend.ai", project:"stable") }`; the table is back to 154 ALIVE /
0 DELETED.

### F9 — three bulk-shaped surfaces, three different answers

Q5 asks for one item per named entity, in input order, with denials and misses told apart. Same batch shape
everywhere: `[owned-and-permitted, exists-but-not-permitted, does-not-exist, duplicate-of-first]`.

**`vfolder bulk-delete` collapses the batch and still mutates.**

```bash
./bai vfolder bulk-delete <owned> <user2's> <000..0ff> <owned-again>     # as user@
# -> a single 403 naming only item 2
# but the owned folder is now status=delete-pending
```

One error for four inputs, no per-item result, no way to tell the miss from the denial — and part of the batch
committed behind an atomic-looking failure. Put the denied item first and nothing is processed, so the outcome
depends on input order.

**`vfolder bulk-purge` returns an aggregate that loses the mapping.**

```bash
./bai vfolder bulk-purge <owned> <user2's> <000..0ff> <owned-again>
# -> {"purged_count": 2, "failed": [ {..user2's, "Insufficient permission"},
#                                    {..000..0ff, "Insufficient permission"} ]}
```

`purged_count: 2` for one folder — the duplicate was processed twice rather than deduplicated. Successes carry
no ids, so no input position maps to an outcome. The miss and the denial share one message.

**`delete_artifacts` reports nothing per item.**

```bash
./bai artifact delete --artifact-ids '["000..0ff","000..0ff"]'
# -> 200 {"artifacts": []}, audit row status=success
```

Two ids that do not exist, "deleted" successfully, empty result. (On real ids the soft delete itself is
correct — `availability` becomes `DELETED`.)

**Only the GraphQL DataLoader path is correct.** `bulk_get_object_storages` and
`bulk_get_storage_namespaces` are the two true `bulk`-kind actions here, reachable by aliasing `node` calls so
the loader coalesces them:

```graphql
{ a: node(id:"<real>") { ... on ObjectStorage { name } }
  b: node(id:"<missing>") { ... on ObjectStorage { name } }
  c: node(id:"<real>") { ... on ObjectStorage { name } } }
```

Admin gets `{a: {...}, b: null, c: {...}}`; a non-admin gets three separate denials each keyed to its own path.
One answer per input, input order preserved, duplicates answered independently, and miss and denial
indistinguishable to the unprivileged caller — which is what Q4 wants. This is the shape the other two should
have.

### F10 — the same file operation needs a different permission depending on API version

| | |
|---|---|
| Declared | BA-7486 recorded the v1/v2 `operation` split as a catalog defect |
| Actual | Confirmed at runtime as a live authorization difference, not just an audit one |
| Blast radius | A grant that permits an operation through one API version forbids it through the other |

Measured by denying user2@ on a folder owned by user@ and reading the permission named in the 403:

| operation | v1 route requires | v2 route requires |
|---|---|---|
| mkdir | `CREATE` | `UPDATE` |
| delete files | `SOFT_DELETE` | `UPDATE` |
| create upload session | `CREATE` | `UPDATE` |
| list files | `READ` (SEARCH) | `READ` (GET) — audit only |

The audit row confirms which action ran: `./bai vfolder mkdir` leaves
`vfolder_mkdir_v2 | vfolder | update | single_entity`. A user granted only `UPDATE` can mkdir through v2 and
not v1; a user granted only `CREATE` can mkdir through v1 and not v2.

### F11 — `NotEnoughPermission` reports every RBAC denial as `role_create_forbidden`

| | |
|---|---|
| Declared | a permission denial on the entity the caller asked for |
| Actual | `errors/permission.py:92` returns `domain=ROLE, operation=CREATE, detail=FORBIDDEN` |
| Blast radius | Every v2 RBAC denial, on every entity, across all three audit slices |

Reading a vfolder you may not read reports `role_create_forbidden`. So does failing to purge an object storage,
or to accept an invitation. Any client keying on `error_code` misclassifies all of them, and the code actively
misleads: nothing about a role, and nothing about creation.

```bash
./bai vfolder get <someone-else's-folder>     # as monitor@
# -> 403 role_create_forbidden | "... lacks permission <Permission.READ: 1> on vfolder ..."
```

The human-readable `msg` is accurate; only the machine-readable code is wrong.

### F12 — route-middleware denials leave no audit row

`AuditLogPolicy` documents "anything that failed or was denied — always" recorded, and for actions that reach
the processor it holds: every mutation and every in-action failure I drove left a row, and RBAC-validator
denials are recorded with `status=denied`. Route middleware is the hole — `superadmin_required` and
`admin_required` reject before the processor runs, so nothing reaches the monitor.

```bash
# three separate non-admin calls, each rejected at auth.py:917
./bai vfs-storage list-all ; ./bai object-storage search --limit 1 ; ./bai admin image search --limit 1
# -> 3 x 403, zero audit rows

# control: a denial that does reach the validator
./bai vfolder delete <someone-else's-folder>
# -> 403, and audit row  delete_vfolder_v2|vfolder|delete|single_entity|<id>|denied
```

Same root cause as agent A's F12 — stated here with my own reproduction for dedupe at merge.

### F13 — secrets reach the client in cleartext on three separate surfaces

Two of these are entity-specific; the third is generic to every v2 create.

**1. Search responses echo the stored secret.** `search_object_storages` and `search_reservoir_registries`
return `secret_key` in the body:

```bash
./bai object-storage search --limit 5
# -> {"items":[{"name":"...","access_key":"AK","secret_key":"SK","endpoint":"...", ...}]}
```

**2. A 409 on create returns the failing `INSERT` with its bound parameters.** When a create trips a unique
constraint, the error body carries the whole SQLAlchemy statement, values included:

```bash
POST /v2/object-storages {"name":"minio-storage", ..., "secret_key":"SUPERSECRET_ba7489b", ...}
# -> 409, 16633-byte body containing:
#    ... $6::VARCHAR) RETURNING object_storages.id]
#    [parameters: ('minio-storage', 'local', 'AKIA_LEAKTEST', 'SUPERSECRET_ba7489b',
#                  'http://127.0.0.1:9000', 'us-east-1')
```

**3. This is not object-storage specific.** `_match_integrity_error`
(`repositories/ops/v2/write_base.py:233`) re-raises the parsed integrity error whenever no domain-specific
check matches, and that error carries the statement and parameters. Any v2 entity create that hits a unique
violation returns its own bound parameters, so every secret-bearing create is affected — confirmed on
`reservoir-registry create`, which trips `uq_artifact_registries_name` through the same path.

The search routes are superadmin-only, which caps severity there. The 409 path is wider: it fires on ordinary
duplicate-name mistakes, the body is large enough to be logged rather than read, and the value it echoes is
the one the caller was told to keep secret. Corroborates agent A's F8 from a third surface.

### F14 — `register_storage_namespace` accepts a storage id that does not exist

No foreign key backs `storage_namespace.storage_id`:

```sql
select conname, pg_get_constraintdef(oid) from pg_constraint
 where conrelid = 'storage_namespace'::regclass;
-- pk_storage_namespace, uq_storage_id_namespace  — no FK to object_storages
```

```bash
./bai storage-namespace register --storage-id 00000000-0000-0000-0000-0000000000ff --namespace ba7489b-ns2
# -> 200, row created
./bai storage-namespace get-by-storage 00000000-0000-0000-0000-0000000000ff
# -> returns the orphan
```

`register` is `global`-kind so no entity lookup happens, and nothing downstream validates the target.

### F15 — five wired v2 actions are reachable only through the v1 REST surface

These carry no v2 route and no CLI command; the only way to reach them is `/folders/…`. Per the audit's own
rule that v2 is the supported surface, each is a gap rather than a working action:

| action | only reachable route |
|---|---|
| `create_vfolder_archive_download_session` | `POST /folders/{id}/request-download-archive` |
| `delete_vfolder_files_async` | `POST /folders/{id}/delete-files-async` |
| `rename_vfolder_file` | `POST /folders/{id}/rename-file` |
| `update_vfolder_sharing_status` | `POST /folders/_/sharing` |
| `update_invited_vfolder_mount_permission` | `POST /folders/_/shared` |

`get_vfolder_legacy_row`, `share_vfolder`, `unshare_vfolder`, `invite_vfolder` and the invitation actions are
also v1-only, but they are already carried by F1/F6/F7.

### F17 — `public_list_shared_vfolders` lists every share in the system to any authenticated user

| | |
|---|---|
| Declared | `vfolder` / `search` / `public_list_shared_vfolders`, `global` / `public` |
| Actual | Returns every `vfolder_permissions` row system-wide, including each shared user's UUID and e-mail |
| Blast radius | Any authenticated account — including one with no vfolder permissions at all — can enumerate who has been given access to what |

`public` is the declared gate and `public` is the gate met, so this is not a gate mismatch. What fails is the
thing that would justify `public`: the result is not limited to shares the caller is party to.

```python
# services/vfolder/services/sharing.py:116
raw_list = await self._vfolder_repository.list_shared_vfolder_permissions(None)
```

The sibling `list_shared_vfolders` passes a vfolder id; the public variant passes `None`, which removes the
filter entirely rather than scoping to the caller.

```bash
# admin@ shares a project folder with user2@
POST /folders/fbdc9dfc-.../share {"permission":"ro","emails":["user2@lablup.com"]}   # -> 201

# monitor@ — neither the owner nor the sharee, and denied on get_vfolder_v2 — reads the share
GET /folders/_/shared
# -> 200 {"shared":[{"vfolder_name":"ba7489b-projshare","owner":"2de2b969-...",
#          "shared_to":{"uuid":"009fb1a4-...","email":"user2@lablup.com"},"perm":"ro"}]}
```

`user@` gets the same. Note that `monitor@` succeeds here while being denied by F1's domain-member grant —
the two reads leak through different mechanisms, so fixing one does not close the other.

I originally scored this row `성공` on the strength of an empty response from all three principals. The
response was empty because no share existed yet, not because it was scoped. Creating one share exposed it.

### F16 — smaller reporting defects

Grouped because each is cheap to fix and none is exploitable on its own.

1. **`_get_storage_client` swallows the real error.** `artifact/service.py:139` wraps the object-storage
   lookup in a bare `except Exception` and falls straight through to the VFS lookup, so whatever actually went
   wrong is replaced by `VFS Storage Not Found (VFS storage with name minio-storage not found.)`. Observed
   masking at least three distinct causes during this run: no `object_storages` row of that name, a
   `StorageProxyNotFound` for the row's host, and a missing storage namespace. The message names VFS storage
   in every case, and VFS is never the thing that failed — it is only the last thing tried. This cost real
   time twice here and produced one wrong inference before the true cause was traced.
2. **`msg` says "Internal server error" on legitimate 404s.** `vfolder_read_not-found`,
   `image_read_not-found` and others carry `"msg": "Internal server error"` alongside a correct 404 status and
   a correct `title`.
3. **Legacy GraphQL denials are HTTP 200.** `rescan_images` and `clear_images` return
   `{"ok": false, "msg": "no permission to execute rescan_images"}` at status 200 rather than a 403, so a
   client cannot distinguish a denial from a failure without parsing the message.
4. **The legacy GraphQL `set_quota_scope` / `unset_quota_scope` mutations bypass the processor.**
   `POST /admin/quota-scopes/set` runs the action and leaves a `set_vfs_quota_scope` audit row; the GraphQL
   mutation for the same effect calls `manager_client.update_quota_scope` directly
   (`gql_legacy/vfolder.py:1540`) and leaves no row and no RBAC check. Two live entry points, one enforced.
5. **`update_invited_vfolder_mount_permission` reports success for a share that does not exist.**
   `POST /folders/_/shared` returned 200 `shared vfolder permission updated` for a (vfolder, user) pair with
   no share between them.
6. **`get_vfolder_quota` / `update_vfolder_quota` fail for the folder's own owner** with
   `400 storage-proxy_request_content-type-mismatch` — the manager cannot parse the storage proxy's error
   response.
7. **`./bai artifact delete --artifact-ids` needs a JSON array**, not a repeatable option. Passing a bare UUID
   raises `json.decoder.JSONDecodeError` client-side; `--help` does not say so.
8. **Artifact-revision audit rows name the artifact, not the revision.** `approve`, `reject`, `cancel_import`,
   `cleanup` and `import` all record `entity_id` = the owning artifact, so the log cannot say which revision
   was acted on. This follows from the field-row design BA-7486 documented, but it is a real loss of audit
   resolution for a moderation workflow.

### Checked and not a defect

Recorded so these are not re-investigated:

- **`search_storage_host_permissions` operation.** Flagged by agent C as catalog `search` vs audit `get`. It
  does not hold: the catalog row declares `get`, `SearchStorageHostPermissionsAction.operation_type()` returns
  `ActionOperationType.GET` (`actions/search_storage_host_permissions.py:40`), and the audit row records
  `get`. The mismatch is between the action's *name* and its operation, not between catalog and audit. The two
  `status=error` rows C saw were my own calls during the storage-proxy outage, since failures are always
  recorded.
- **`RESTORE` maps to `SOFT_DELETE`.** Deliberate and documented at `actions/types.py:141` — undoing a soft
  delete reaches nothing the deleter could not already reach.
- **`no row` after a successful read.** `AuditLogPolicy` opt-in behaviour, and no read operation is opted in
  here.
- **`delete_artifacts` soft-delete.** Sets `availability = DELETED`; the row and its revisions correctly remain.

### Confirmations of BA-7486

| action | static | runtime |
|---|---|---|
| `preload_image` | `W` wired, never called | `{ok:false, msg:"Not implemented."}` |
| `unload_image` | `W` | `{ok:false, msg:"Not implemented."}` |
| `list_hugging_face_registry` | `W` | no route, no CLI, no GraphQL field |
| `list_reservoir_registries` | `W` | same |
| `get_artifact_revisions` | `W` | same |
| `purge_images`, `set_image_resource_limit_by_id`, `clear_image_custom_resource_limit_by_id` | `W` | no caller |
| `restore_artifacts` | `O` UPDATE should be RESTORE | audit row reads `restore_artifacts \| global \| update` |
| `handle_harbor_webhook` | `G` conditional secret | condition false on every registry — see F4 |

Also confirmed, and referenced rather than re-filed: agent A's finding that **every `global`-kind action writes
`entity_type='global'`** instead of its declared type
(`actions/v2/global_scope/monitor/audit_log.py:73`). It shows up throughout my registry and storage concerns —
`create_vfs_storage`, `create_object_storage`, `register_storage_namespace`, `scan_artifacts`,
`delete_artifacts`, `restore_artifacts`, `alias_image`, `update_image`, `rescan_images`, `clear_images`,
`set_vfs_quota_scope` and every other `global`-kind row below. `single_entity` and `scope` kinds record their
declared type correctly.

## Per-action results

| concern | entity_type | operation | action_name | declared kind/gate | route exercised | admin result | non-admin result | audit row match | Q verdicts | evidence |
|---|---|---|---|---|---|---|---|---|---|---|
| artifact_registry | vfs_storage | create | create_vfs_storage | global/permission | cli:vfs-storage create | ok | 403 backendai_generic_forbidden | mismatch: entity_type=global (catalog vfs_storage) | Q1 ok, Q2 mismatch, Q3 mismatch, Q4 n/a, Q5 n/a | `./bai vfs-storage create --name ba7489b-vfs1 --host 127.0.0.1 --base-path /tmp/ba7489b` |
| artifact_registry | vfs_storage | get | get_vfs_storage | single_entity/permission | cli:vfs-storage get | ok / 404 on miss | 403 backendai_generic_forbidden | match (entity_type=vfs_storage) | Q1 ok, Q2 mismatch, Q3 ok, Q4 mismatch, Q5 n/a | `./bai vfs-storage get <id>` vs `... 000..0ff` |
| artifact_registry | vfs_storage | update | update_vfs_storage | single_entity/permission | cli:vfs-storage update | ok / 404 on miss | 403 backendai_generic_forbidden | match | Q1 ok, Q2 mismatch, Q3 ok, Q4 mismatch, Q5 n/a | `./bai vfs-storage update --id <id> --base-path /tmp/ba7489b2` |
| artifact_registry | vfs_storage | purge | purge_vfs_storage | single_entity/permission | cli:vfs-storage delete | 404 on miss | 403 backendai_generic_forbidden | match | Q1 ok, Q2 mismatch, Q3 ok, Q4 mismatch, Q5 n/a | `./bai vfs-storage delete --id <id>` |
| artifact_registry | vfs_storage | search | list_vfs_storages | global/permission | cli:vfs-storage list-all | ok | 403 backendai_generic_forbidden | no row (successful read — policy) | Q1 ok, Q2 ok, Q3 n/a, Q4 n/a, Q5 n/a | `./bai vfs-storage list-all` |
| artifact_registry | vfs_storage | search | search_vfs_storages | global/permission | cli:vfs-storage search | ok | 403 backendai_generic_forbidden | no row (successful read — policy) | Q1 ok, Q2 ok, Q3 n/a, Q4 n/a, Q5 n/a | `./bai vfs-storage search --limit 2` |
| artifact_registry | vfs_storage | lookup | lookup_vfs_storage | lookup/permission | none (internal owner resolution) | not exercised | not exercised | no row | Q1 internal-only, Q2 n/a, Q3 n/a, Q4 n/a, Q5 n/a | no client route; fires inside other actions |
| artifact_registry | vfs_storage | get | get_vfs_quota_scope | global/permission | rest-v1:GET /admin/quota-scopes/{host}/{qsid} | 200 | 403 backendai_generic_forbidden | no row (successful read — policy) | Q1 ok, Q2 ok, Q3 n/a, Q4 n/a, Q5 n/a | `GET /admin/quota-scopes/local:volume1/user:<uuid>` |
| artifact_registry | vfs_storage | search | search_vfs_quota_scopes | global/permission | rest-v1:POST /admin/quota-scopes/search | 200 | 403 backendai_generic_forbidden | no row (successful read — policy) | Q1 ok, Q2 ok, Q3 n/a, Q4 n/a, Q5 n/a | `POST /admin/quota-scopes/search {}` |
| artifact_registry | vfs_storage | update | set_vfs_quota_scope | global/permission | rest-v1:POST /admin/quota-scopes/set **and** gql:set_quota_scope | 200 both routes | 403 on REST; GQL route not reached by non-admin | REST: mismatch entity_type=global. **GQL: no row** | Q1 ok, Q2 mismatch, Q3 mismatch, Q4 n/a, Q5 n/a | `POST /admin/quota-scopes/set` leaves a row; `mutation { set_quota_scope(...) }` leaves none — F16.4 |
| artifact_registry | vfs_storage | delete | unset_vfs_quota_scope | global/permission | rest-v1:POST /admin/quota-scopes/unset **and** gql:unset_quota_scope | 200 both routes | 403 on REST | REST: mismatch entity_type=global. **GQL: no row** | Q1 ok, Q2 mismatch, Q3 mismatch, Q4 n/a, Q5 n/a | same as above — F16.4 |
| artifact_registry | object_storage | create | create_object_storage | global/permission | cli:object-storage create | ok | 403 backendai_generic_forbidden | mismatch: entity_type=global (catalog object_storage) | Q1 ok, Q2 mismatch, Q3 mismatch, Q4 n/a, Q5 n/a | `./bai object-storage create --name ba7489b-obj1 ...` |
| artifact_registry | object_storage | get | get_object_storage | single_entity/permission | cli:object-storage get | ok / 404 on miss | 403 backendai_generic_forbidden | match | Q1 ok, Q2 mismatch, Q3 ok, Q4 mismatch, Q5 n/a | `./bai object-storage get <id>` |
| artifact_registry | object_storage | update | update_object_storage | single_entity/permission | cli:object-storage update | ok | 403 backendai_generic_forbidden | match | Q1 ok, Q2 mismatch, Q3 ok, Q4 mismatch, Q5 n/a | `./bai object-storage update --id <id> ...` |
| artifact_registry | object_storage | purge | purge_object_storage | single_entity/permission | cli:object-storage delete | ok | 403 backendai_generic_forbidden | match | Q1 ok, Q2 mismatch, Q3 ok, Q4 mismatch, Q5 n/a | `./bai object-storage delete --id <id>` |
| artifact_registry | object_storage | search | search_object_storages | global/permission | cli:object-storage search | ok (**leaks secret_key in cleartext**) | 403 backendai_generic_forbidden | no row (successful read — policy) | Q1 ok, Q2 ok, Q3 n/a, Q4 n/a, Q5 n/a | `./bai object-storage search --limit 5` returns `secret_key` — F13 |
| artifact_registry | object_storage | search | list_object_storages | global/permission | gql:objectStorages | ok | 403 (superadmin decorator) | no row (successful read — policy) | Q1 ok, Q2 ok, Q3 n/a, Q4 n/a, Q5 n/a | `./bai gql --v2 '{ objectStorages { ... } }'` |
| artifact_registry | object_storage | get | bulk_get_object_storages | bulk/permission | gql:node(id:) via DataLoader (aliased batch) | one answer per input, in order; miss=null | one denial per input, in order; miss and denial identical | no row (successful read — policy) | Q1 ok, Q2 ok, Q3 n/a, Q4 ok, **Q5 ok** | `{ a: node(id:X) b: node(id:MISS) c: node(id:X) }` -> a/b/c each answered |
| artifact_registry | storage_namespace | create | register_storage_namespace | global/permission | cli:storage-namespace register | ok — **accepts a nonexistent storage_id** | 403 backendai_generic_forbidden | mismatch: entity_type=global (catalog storage_namespace) | Q1 ok, Q2 mismatch, Q3 mismatch, Q4 n/a, Q5 n/a | `./bai storage-namespace register --storage-id 000..0ff --namespace ba7489b-ns2` -> 200 — F14 |
| artifact_registry | storage_namespace | purge | unregister_storage_namespace | single_entity/permission | cli:storage-namespace unregister | ok | 403 backendai_generic_forbidden | match | Q1 ok, Q2 mismatch, Q3 ok, Q4 mismatch, Q5 n/a | `./bai storage-namespace unregister --storage-id <id> --namespace ba7489b-ns1` |
| artifact_registry | storage_namespace | search | search_storage_namespaces | global/permission | cli:storage-namespace search | ok | 403 backendai_generic_forbidden | no row (successful read — policy) | Q1 ok, Q2 ok, Q3 n/a, Q4 n/a, Q5 n/a | `./bai storage-namespace search --limit 5` |
| artifact_registry | storage_namespace | search | search_storage_namespaces_of_storage | global/permission | cli:storage-namespace get-by-storage | ok — returns rows for a nonexistent storage id | 403 backendai_generic_forbidden | no row (successful read — policy) | Q1 ok, Q2 ok, Q3 n/a, Q4 mismatch, Q5 n/a | `./bai storage-namespace get-by-storage 000..0ff` -> returns the orphan row — F14 |
| artifact_registry | storage_namespace | get | bulk_get_storage_namespaces | bulk/permission | gql:node(id:) via DataLoader (aliased batch) | one answer per input, in order; miss=null | one denial per input, in order; miss and denial identical | no row (successful read — policy) | Q1 ok, Q2 ok, Q3 n/a, Q4 ok, **Q5 ok** | `{ a: node(id:NS) b: node(id:MISS) c: node(id:NS) }` |
| artifact_registry | storage_namespace | lookup | lookup_storage_namespace | lookup/permission | none (internal owner resolution) | not exercised | not exercised | no row | Q1 internal-only, Q2 n/a, Q3 n/a, Q4 n/a, Q5 n/a | no client route |
| artifact_registry | artifact_registry | create | create_hugging_face_registry | global/permission | cli:huggingface-registry create | ok | 403 backendai_generic_forbidden | mismatch: entity_type=global | Q1 ok, Q2 mismatch, Q3 mismatch, Q4 mismatch, Q5 n/a | `./bai huggingface-registry create --name ba7489b-hf1 --url https://huggingface.co` |
| artifact_registry | artifact_registry | create | create_reservoir_registry | global/permission | cli:reservoir-registry create | ok | 403 backendai_generic_forbidden | mismatch: entity_type=global | Q1 ok, Q2 mismatch, Q3 mismatch, Q4 mismatch, Q5 n/a | `./bai reservoir-registry create --name ba7489b-res1 ...` |
| artifact_registry | artifact_registry | delete | delete_hugging_face_registry | single_entity/permission | cli:huggingface-registry delete | ok | 403 backendai_generic_forbidden | match | Q1 ok, Q2 mismatch, Q3 ok, Q4 mismatch, Q5 n/a | `./bai huggingface-registry delete --id <id>` |
| artifact_registry | artifact_registry | delete | delete_reservoir_registry | single_entity/permission | cli:reservoir-registry delete | ok | 403 backendai_generic_forbidden | match | Q1 ok, Q2 mismatch, Q3 ok, Q4 mismatch, Q5 n/a | `./bai reservoir-registry delete --id <id>` |
| artifact_registry | artifact_registry | get | get_hugging_face_registry | single_entity/permission | cli:huggingface-registry get | ok / 404 on miss | 403 backendai_generic_forbidden | match | Q1 ok, Q2 mismatch, Q3 ok, Q4 mismatch, Q5 n/a | `./bai huggingface-registry get <id>` |
| artifact_registry | artifact_registry | get | get_reservoir_registry | single_entity/permission | cli:reservoir-registry get | ok / 404 on miss | 403 backendai_generic_forbidden | match | Q1 ok, Q2 mismatch, Q3 ok, Q4 mismatch, Q5 n/a | `./bai reservoir-registry get <id>` |
| artifact_registry | artifact_registry | update | update_hugging_face_registry | single_entity/permission | cli:huggingface-registry update | ok / 404 on miss | 403 backendai_generic_forbidden | match | Q1 ok, Q2 mismatch, Q3 ok, Q4 mismatch, Q5 n/a | `./bai huggingface-registry update --id <id> --name ba7489b-hf1b` |
| artifact_registry | artifact_registry | update | update_reservoir_registry | single_entity/permission | cli:reservoir-registry update | ok / 404 on miss | 403 backendai_generic_forbidden | match | Q1 ok, Q2 mismatch, Q3 ok, Q4 mismatch, Q5 n/a | `./bai reservoir-registry update --id <id> --name x` |
| artifact_registry | artifact_registry | search | search_hugging_face_registries | global/permission | cli:huggingface-registry search | ok | 403 backendai_generic_forbidden | no row (successful read — policy) | Q1 ok, Q2 mismatch, Q3 n/a, Q4 mismatch, Q5 n/a | `./bai huggingface-registry search --limit 3` |
| artifact_registry | artifact_registry | search | search_reservoir_registries | global/permission | cli:reservoir-registry search | ok (**leaks secret_key**) | 403 backendai_generic_forbidden | no row (successful read — policy) | Q1 ok, Q2 mismatch, Q3 n/a, Q4 mismatch, Q5 n/a | `./bai reservoir-registry search --limit 3` returns `secret_key` — F13 |
| artifact_registry | artifact_registry | get | get_artifact_registry_meta | single_entity/permission | cli:artifact-registry get / rest:GET /v2/artifact-registries/{id} | ok / 404 on miss | 403 role_create_forbidden — **identical for miss and denial** | match (entity_type=artifact_registry) | Q1 ok, **Q2 ok**, Q3 ok, **Q4 ok**, Q5 n/a | only artifact route on `auth_required`; `./bai artifact-registry get <id>` vs `000..0ff` as user@ — same 403 |
| artifact_registry | artifact_registry | get | get_artifact_registry_metas | global/permission | gql:artifactRegistryMetas | ok | 403 (superadmin decorator) | no row (successful read — policy) | Q1 ok, Q2 ok, Q3 n/a, Q4 n/a, Q5 n/a | reached through the v2 GraphQL query root |
| artifact_registry | artifact_registry | search | search_artifact_registries | global/permission | gql:artifactRegistries | ok | 403 (superadmin decorator) | no row (successful read — policy) | Q1 ok, Q2 ok, Q3 n/a, Q4 n/a, Q5 n/a | adapter `api/adapters/artifact_registry` |
| artifact_registry | artifact_registry | get | get_hugging_face_registries | global/permission | gql (list resolver) | ok | 403 (superadmin decorator) | no row (successful read — policy) | Q1 ok, Q2 ok, Q3 n/a, Q4 n/a, Q5 n/a | covered by the search route above |
| artifact_registry | artifact_registry | get | get_reservoir_registries | global/permission | gql (list resolver) | ok | 403 (superadmin decorator) | no row (successful read — policy) | Q1 ok, Q2 ok, Q3 n/a, Q4 n/a, Q5 n/a | covered by the search route above |
| artifact_registry | artifact_registry | search | list_hugging_face_registry | global/permission | **none** | not exercised — no caller | not exercised | no row | **Q1 unreachable**, Q2 n/a, Q3 n/a, Q4 n/a, Q5 n/a | confirms BA-7486 `W` (wired, never called) — no route, no CLI, no GQL field |
| artifact_registry | artifact_registry | search | list_reservoir_registries | global/permission | **none** | not exercised — no caller | not exercised | no row | **Q1 unreachable**, Q2 n/a, Q3 n/a, Q4 n/a, Q5 n/a | confirms BA-7486 `W` |
| artifact_registry | artifact_registry | lookup | lookup_artifact_registry | lookup/public | none (internal owner resolution) | not exercised | not exercised | no row | Q1 internal-only, Q2 n/a, Q3 n/a, Q4 n/a, Q5 n/a | no client route |
| artifact_registry | artifact | get | get_artifact | single_entity/permission | cli:artifact get | ok on a real artifact / 404 on miss | 403 backendai_generic_forbidden (route middleware) | no row (successful read — policy) | Q1 ok, Q2 mismatch, Q3 n/a, Q4 mismatch, Q5 n/a | `./bai artifact get e39af1b0-…` returned the scanned gpt2 record |
| artifact_registry | artifact | update | update_artifact | single_entity/permission | cli:artifact update | ok on a real artifact / 404 on miss | 403 backendai_generic_forbidden | match (`update_artifact \| artifact \| update \| single_entity`) | Q1 ok, Q2 mismatch, Q3 ok, Q4 mismatch, Q5 n/a | `./bai artifact update e39af1b0-… --description ba7489b-desc` |
| artifact_registry | artifact | search | search_artifacts | global/permission | cli:admin artifact search | ok (empty) | 403 backendai_generic_forbidden | no row (successful read — policy) | Q1 ok, Q2 ok, Q3 n/a, Q4 n/a, Q5 n/a | `./bai admin artifact search --limit 2` |
| artifact_registry | artifact | delete | delete_artifacts | global/permission | cli:artifact delete | 200 `{"artifacts": []}` for two nonexistent ids, audit status=success | 403 backendai_generic_forbidden | mismatch: entity_type=global (catalog artifact) | Q1 ok, Q2 mismatch, Q3 mismatch, Q4 mismatch, **Q5 mismatch** | `./bai artifact delete --artifact-ids '["000..0ff","000..0ff"]'` -> empty list, no per-item answer — F9 |
| artifact_registry | artifact | update | restore_artifacts | global/permission | cli:artifact restore | 200 `{"artifacts": []}` for a nonexistent id | 403 backendai_generic_forbidden | mismatch: entity_type=global **and operation=update** (a DELETED->ALIVE transition) | Q1 ok, Q2 mismatch, Q3 mismatch, Q4 mismatch, **Q5 mismatch** | `./bai artifact restore --artifact-ids '["000..0ff"]'`; audit row `restore_artifacts\|global\|update` confirms BA-7486 `O` |
| artifact_registry | artifact | search | search_artifacts_with_revisions | global/permission | gql:artifacts | ok (empty) | 403 user_auth_forbidden | no row (successful read — policy) | Q1 ok, Q2 ok, Q3 n/a, Q4 n/a, Q5 n/a | `./bai gql --v2 '{ artifacts(first:3) { count } }'` |
| artifact_registry | artifact | create | scan_artifacts | global/permission | gql:scanArtifacts | ok — 2 artifacts scanned from HuggingFace Hub | 403 user_auth_forbidden | match — entity_type=global vs catalog artifact | Q1 ok, Q2 ok, Q3 mismatch, Q4 n/a, Q5 n/a | `mutation { scanArtifacts(input:{artifactType:MODEL, registryId:X, limit:2, search:"gpt2"}) { artifacts { id name } } }`; **fails with a bare 404 for any registry not named in the proxy's TOML — F6** |
| artifact_registry | artifact | get | retrieve_models | global/permission | gql:scanArtifactModels | ok | 403 user_auth_forbidden | match — entity_type=global | Q1 ok, Q2 ok, Q3 mismatch, Q4 n/a, Q5 n/a | `mutation { scanArtifactModels(input:{registryId:X, models:[{modelId:"gpt2"}]}) ... }` |
| artifact_registry | artifact | get | retrieve_model | global/permission | gql:scanArtifactModels (single-model input) | ok — resolved sshleifer/tiny-gpt2 and returned its revision | 403 user_auth_forbidden | no row (successful read — policy) | Q1 ok, Q2 ok, Q3 n/a, Q4 n/a, Q5 n/a | `mutation { scanArtifactModels(input:{registryId:X, models:[{modelId:"sshleifer/tiny-gpt2"}]}) { artifactRevision { edges { node { id status } } } } }` |
| artifact_registry | artifact | create | delegate_scan_artifacts | global/permission | gql:delegateScanArtifacts | not exercised — requires a reachable delegatee reservoir | 403 user_auth_forbidden | no row | Q1 ok, Q2 ok, Q3 n/a, Q4 n/a, Q5 n/a | no second reservoir instance available in this stack |
| artifact_registry | artifact | create | delegate_import_artifact_revision_batch | global/permission | gql:delegateImportArtifacts | not exercised — requires a reachable delegatee reservoir | 403 user_auth_forbidden | no row | Q1 ok, Q2 ok, Q3 n/a, Q4 n/a, Q5 n/a | BA-7486 already records the catalog/audit entity_type split (catalog `artifact` / audit `global`) |
| artifact_registry | artifact | search | search_artifact_revisions | global/permission | gql:artifactRevisions | ok (empty) | 403 user_auth_forbidden | no row (successful read — policy) | Q1 ok, Q2 ok, Q3 n/a, Q4 n/a, Q5 n/a | `{ artifactRevisions(first:3) { count } }` |
| artifact_registry | artifact | search | get_artifact_revisions | single_entity/permission | **none** | not exercised — no caller | not exercised | no row | **Q1 unreachable**, Q2 n/a, Q3 n/a, Q4 n/a, Q5 n/a | confirms BA-7486 `W` |
| artifact_registry | artifact | update | upsert_artifacts | global/permission | **none (processor bypassed)** | not exercised — the service calls its own method directly | not exercised | no row | **Q1 unreachable via processor**, Q2 n/a, Q3 n/a, Q4 n/a, Q5 n/a | confirms BA-7486 `W`+`O` (`artifact/service.py:334,651`) |
| artifact_registry | artifact | lookup | lookup_artifact_revision_owner | lookup/permission | none (internal owner resolution) | not exercised | not exercised | no row | Q1 internal-only, Q2 n/a, Q3 n/a, Q4 n/a, Q5 n/a | fires inside revision actions |
| artifact_registry | artifact | lookup | lookup_bulk_artifact_revision_owner | lookup/permission | **none** | not exercised — unreachable | not exercised | no row | **Q1 unreachable**, Q2 n/a, Q3 n/a, Q4 n/a, Q5 n/a | confirms BA-7486 `W` (domain wires no bulk field operation) |
| artifact_registry | artifact_revision | get | get_artifact_revision | single_entity/permission | cli:artifact revision get | ok on a real revision | 403 backendai_generic_forbidden (route middleware) | no row (successful read — policy) | Q1 ok, Q2 mismatch, Q3 n/a, Q4 mismatch, Q5 n/a | `./bai artifact revision get 6402315c-…` returned status SCANNED, size 5632417295 |
| artifact_registry | artifact_revision | update | approve_artifact_revision | single_entity/permission | cli:artifact revision approve | 400 artifact_access_bad-request — correctly refuses a non-verified revision | 403 backendai_generic_forbidden | match (entity_id = the **artifact**, not the revision) | Q1 ok, Q2 mismatch, Q3 mismatch, Q4 n/a, Q5 n/a | `./bai artifact revision approve 6402315c-…` -> `Only verified artifacts could be approved` |
| artifact_registry | artifact_revision | update | reject_artifact_revision | single_entity/permission | cli:artifact revision reject | ok — status becomes REJECTED | 403 backendai_generic_forbidden | match (entity_id = the artifact) | Q1 ok, Q2 mismatch, Q3 mismatch, Q4 n/a, Q5 n/a | `./bai artifact revision reject 6402315c-…` |
| artifact_registry | artifact_revision | update | cancel_import | single_entity/permission | cli:artifact revision cancel-import | **ok — resets ANY status to SCANNED, including REJECTED and AVAILABLE** | 403 backendai_generic_forbidden | match (entity_id = the artifact) | Q1 ok, Q2 mismatch, Q3 mismatch, Q4 n/a, Q5 n/a | `./bai artifact revision cancel-import <available-revision>` -> SCANNED while the files stay in MinIO — **F4** |
| artifact_registry | artifact_revision | delete | cleanup_artifact_revision | single_entity/permission | cli:artifact revision cleanup | ok on AVAILABLE (bucket emptied, 9 objects -> 0); 400 on any other status | 403 backendai_generic_forbidden | match (entity_id = the artifact) | Q1 ok, Q2 mismatch, Q3 mismatch, Q4 n/a, Q5 n/a | `./bai artifact revision cleanup <available-revision>`; refuses SCANNED — the other half of **F4** |
| artifact_registry | artifact_revision | create | import_artifact_revision | single_entity/permission | gql:importArtifacts | ok — SCANNED -> PULLING -> AVAILABLE, files land in MinIO. **bgtask** returned as `tasks { taskId }` | 403 user_auth_forbidden | match (entity_id = the artifact, not the revision) | Q1 ok, Q2 mismatch, Q3 mismatch, Q4 n/a, Q5 n/a | `mutation { importArtifacts(input:{artifactRevisionIds:[X]}) { tasks { taskId } } }`; imported sshleifer/tiny-gpt2 (9 objects) |
| artifact_registry | artifact_revision | create | associate_with_storage | single_entity/permission | none | not exercised — processor bypassed (`revision/service.py:586`) — BA-7486 `W` | not exercised | no row | Q1 unreachable, Q2 n/a, Q3 n/a, Q4 n/a, Q5 n/a | processor bypassed (`revision/service.py:586`) — BA-7486 `W` |
| artifact_registry | artifact_revision | delete | disassociate_with_storage | single_entity/permission | none | not exercised — processor bypassed (`revision/service.py:676`) — BA-7486 `W` | not exercised | no row | Q1 unreachable, Q2 n/a, Q3 n/a, Q4 n/a, Q5 n/a | processor bypassed (`revision/service.py:676`) — BA-7486 `W` |
| artifact_registry | artifact_revision | get | get_artifact_revision_readme | single_entity/permission | gql/rest (blocked upstream) | not exercised — requires a scanned revision | not exercised | no row | Q1 unreachable, Q2 n/a, Q3 n/a, Q4 n/a, Q5 n/a | requires a scanned revision |
| artifact_registry | artifact_revision | get | get_artifact_revision_verification_result | single_entity/permission | gql/rest (blocked upstream) | not exercised — requires an imported revision | not exercised | no row | Q1 unreachable, Q2 n/a, Q3 n/a, Q4 n/a, Q5 n/a | requires an imported revision |
| artifact_registry | artifact_revision | get | get_download_presigned_url | single_entity/permission | gql:getPresignedDownloadUrl | ok on AVAILABLE — returns a working signed MinIO URL; refuses any other status | 403 user_auth_forbidden | no row (successful read — policy) | Q1 ok, Q2 mismatch, Q3 n/a, Q4 n/a, Q5 n/a | `mutation { getPresignedDownloadUrl(input:{artifactRevisionId:X, key:"config.json"}) { presignedUrl } }`; the URL is a bearer credential handed out with no audit row |
| artifact_registry | artifact_revision | get | get_download_progress | single_entity/permission | gql/rest (blocked upstream) | not exercised — requires an in-flight import bgtask | not exercised | no row | Q1 unreachable, Q2 n/a, Q3 n/a, Q4 n/a, Q5 n/a | requires an in-flight import bgtask |
| artifact_registry | artifact_revision | update | get_upload_presigned_url | single_entity/permission | gql:getPresignedUploadUrl | 403 artifact_update_forbidden — correctly refuses a readonly artifact | 403 user_auth_forbidden | match (status=error) | Q1 ok, Q2 mismatch, Q3 mismatch, Q4 n/a, Q5 n/a | `mutation { getPresignedUploadUrl(input:{artifactRevisionId:X, key:"ba7489b.txt"}) { presignedUrl } }` |
| vfolder | vfolder | get | get_vfolder_v2 | single_entity/permission | cli:vfolder get / rest:GET /v2/vfolders/{id} | ok | **ok — any domain member reads any other user's vfolder** | no row on success (read, opt-in policy); denials recorded | Q1 ok, **Q2 mismatch**, Q3 n/a, **Q4 mismatch**, Q5 n/a | `./bai vfolder get <u1-folder>` as user2@ -> 200 with owner e-mail, quota scope, name — **F1** |
| vfolder | vfolder | get | get_vfolder_legacy_row | single_entity/permission | rest-v1:GET /folders/{id} | 404 (admin does not own it) | 404 for a non-owner — correct | no row (successful read — policy) | Q1 ok, **Q2 ok**, Q3 n/a, **Q4 ok**, Q5 n/a | `GET /folders/<u1-folder>` as user2@ -> 404; the v1 route enforces the ownership scope the v2 route drops — **F1** |
| vfolder | vfolder | get | get_vfolder | single_entity/permission | rest-v1:GET /folders/{id} (v1 alias) | 404 | 404 | no row (successful read — policy) | Q1 ok, Q2 ok, Q3 n/a, Q4 ok, Q5 n/a | same route as `get_vfolder_legacy_row` |
| vfolder | vfolder | create | create_vfolder_v2 | scope/permission | cli:vfolder create | ok | ok (own user scope) | match (entity_type=vfolder, kind=scope) | Q1 ok, Q2 ok, Q3 ok, Q4 n/a, Q5 n/a | `./bai vfolder create --name ba7489b-vf1 --host local:volume1` |
| vfolder | vfolder | create | create_vfolder | scope/permission | rest-v1:POST /folders | ok | ok | match | Q1 ok, Q2 ok, Q3 ok, Q4 n/a, Q5 n/a | `POST /folders {"name":"ba7489b-vf1v1","host":"local:volume1",...}` -> 201 |
| vfolder | vfolder | create | create_vfolder_in_project | scope/permission | cli:vfolder project-create | ok | 403 role_create_forbidden at project scope | match | Q1 ok, Q2 ok, Q3 ok, Q4 n/a, Q5 n/a | `./bai vfolder project-create <proj> --name ba7489b-vf-proj --host local:volume1` as user@ -> denied at `scope/validator/rbac.py:62` |
| vfolder | vfolder | delete | delete_vfolder_v2 | single_entity/permission | cli:vfolder delete | 404 on miss | 403 role_create_forbidden (SOFT_DELETE) — identical for miss and denial | match | Q1 ok, Q2 ok, Q3 ok, **Q4 ok**, Q5 n/a | `./bai vfolder delete <u1-folder>` as user2@ vs `000..0ff` — same 403 from `rbac.py:52` |
| vfolder | vfolder | delete | move_to_trash_vfolder | single_entity/permission | rest-v1:DELETE /folders | ok | 403 role_create_forbidden | match | Q1 ok, Q2 ok, Q3 ok, Q4 ok, Q5 n/a | `DELETE /folders {"vfolder_id":"<id>"}` as user2@ -> 403 |
| vfolder | vfolder | purge | purge_vfolder_v2 | single_entity/permission | cli:vfolder purge | 404 on miss | 403 role_create_forbidden (HARD_DELETE) — identical for miss and denial | match | Q1 ok, Q2 ok, Q3 ok, **Q4 ok**, Q5 n/a | `./bai vfolder purge <id> --force` |
| vfolder | vfolder | purge | purge_vfolder | single_entity/permission | rest-v1:POST /folders/purge | ok | 403 role_create_forbidden | match | Q1 ok, Q2 ok, Q3 ok, Q4 ok, Q5 n/a | `POST /folders/purge {"vfolder_id":"<id>"}` |
| vfolder | vfolder | purge | delete_forever_vfolder | single_entity/permission | rest-v1:POST /folders/delete-from-trash-bin | ok | 403 role_create_forbidden | match | Q1 ok, Q2 ok, Q3 ok, Q4 ok, Q5 n/a | `POST /folders/delete-from-trash-bin {"vfolder_id":"000..0ff"}` as user@ -> 403 |
| vfolder | vfolder | purge | force_delete_vfolder | single_entity/permission | rest-v1:DELETE /folders/{id}/force | ok | 403 role_create_forbidden | match | Q1 ok, Q2 ok, Q3 ok, Q4 ok, Q5 n/a | `DELETE /folders/<u1-folder>/force` as user2@ -> 403 |
| vfolder | vfolder | restore | restore_vfolder_from_trash | single_entity/permission | cli:vfolder restore / rest-v1:POST /folders/restore-from-trash-bin | 404 on miss | 403 role_create_forbidden (SOFT_DELETE — deliberate, `types.py:141`) | match | Q1 ok, Q2 ok, Q3 ok, Q4 ok, Q5 n/a | RESTORE maps to SOFT_DELETE by documented design, not a defect |
| vfolder | vfolder | create | clone_vfolder_v2 | single_entity/permission | cli:vfolder clone | 400 vfolder_access_invalid-parameters on miss | 403 role_create_forbidden (CREATE on the source) | match (status=error) | Q1 ok, Q2 ok, Q3 no row, **Q4 mismatch**, Q5 n/a | admin gets 400 `No such vfolder.` while a non-admin gets 403 — status differs by caller, but the leak only reaches an admin |
| vfolder | vfolder | create | clone_vfolder | single_entity/permission | rest-v1:POST /folders/{id}/clone | reached | 403 role_create_forbidden | match (status=error) | Q1 ok, Q2 ok, Q3 no row, Q4 ok, Q5 n/a | v1 route behind `_vfolder_resolver` |
| vfolder | vfolder | update | vfolder_mkdir_v2 | single_entity/permission | cli:vfolder mkdir | 404 on miss | 403 role_create_forbidden — **UPDATE** | match (`vfolder_mkdir_v2\|vfolder\|update\|single_entity`) | Q1 ok, **Q2 mismatch**, Q3 ok, Q4 ok, Q5 n/a | `./bai vfolder mkdir <id> /d` requires UPDATE; the v1 route requires CREATE for the same effect — **F10** |
| vfolder | vfolder | create | vfolder_mkdir | single_entity/permission | rest-v1:POST /folders/{id}/mkdir | ok | 403 role_create_forbidden — **CREATE** | match | Q1 ok, **Q2 mismatch**, Q3 ok, Q4 ok, Q5 n/a | same effect as `vfolder_mkdir_v2`, different permission bit — **F10** |
| vfolder | vfolder | update | delete_vfolder_files_v2 | single_entity/permission | cli:vfolder rm | 404 on miss | 403 role_create_forbidden — **UPDATE** | match | Q1 ok, **Q2 mismatch**, Q3 ok, Q4 ok, Q5 n/a | `./bai vfolder rm <id> a` — **F10** |
| vfolder | vfolder | delete | delete_vfolder_files | single_entity/permission | rest-v1:POST /folders/{id}/delete-files | ok | 403 role_create_forbidden — **SOFT_DELETE** | match | Q1 ok, **Q2 mismatch**, Q3 ok, Q4 ok, Q5 n/a | same effect, third permission bit — **F10** |
| vfolder | vfolder | delete | delete_vfolder_files_async | single_entity/permission | rest-v1:POST /folders/{id}/delete-files-async | 202 (bgtask) | 403 role_create_forbidden | match | Q1 ok, Q2 mismatch, Q3 ok, Q4 ok, Q5 n/a | `POST /folders/<id>/delete-files-async {"files":[...],"recursive":false}` -> 202; bgtask `delete_vfolder_files` |
| vfolder | vfolder | get | list_vfolder_files_v2 | single_entity/permission | cli:vfolder ls | 404 on miss | 403 role_create_forbidden — READ | no row (successful read — policy) | Q1 ok, Q2 ok, Q3 n/a, Q4 ok, Q5 n/a | `./bai vfolder ls <id> /` — GET vs v1 SEARCH; same permission bit, audit only |
| vfolder | vfolder | search | list_vfolder_files | single_entity/permission | rest-v1:GET /folders/{id}/files | ok | **404 for a non-owner — correct** | no row (successful read — policy) | Q1 ok, Q2 ok, Q3 n/a, **Q4 ok**, Q5 n/a | `GET /folders/<u1-folder>/files?path=.` as user2@ -> 404; contrast with `get_vfolder_v2` — **F1** |
| vfolder | vfolder | update | move_vfolder_file_v2 | single_entity/permission | cli:vfolder mv | 404 on miss | 403 role_create_forbidden — UPDATE | match | Q1 ok, Q2 ok, Q3 ok, Q4 ok, Q5 n/a | `./bai vfolder mv <id> a b` |
| vfolder | vfolder | update | move_vfolder_file | single_entity/permission | rest-v1:POST /folders/{id}/move-file | 400 vfolder_generic_bad-request from the storage proxy | 403 role_create_forbidden | match (status=error) | Q1 ok, Q2 ok, Q3 no row, Q4 ok, Q5 n/a | `POST /folders/<id>/move-file {"src":"a.txt","dst":"b.txt"}` |
| vfolder | vfolder | update | rename_vfolder_file | single_entity/permission | rest-v1:POST /folders/{id}/rename-file | 400 vfolder_generic_bad-request from the storage proxy | 403 role_create_forbidden | match (status=error) | Q1 ok, Q2 ok, Q3 no row, Q4 ok, Q5 n/a | `POST /folders/<id>/rename-file {"target_path":...,"new_name":...}` |
| vfolder | vfolder | update | create_vfolder_upload_session_v2 | single_entity/permission | rest:POST /v2/vfolders/{id}/upload-session | ok | 403 role_create_forbidden — UPDATE | match | Q1 ok, **Q2 mismatch**, Q3 ok, Q4 ok, Q5 n/a | v1 declares CREATE for the same effect — **F10** |
| vfolder | vfolder | create | create_vfolder_upload_session | single_entity/permission | rest-v1:POST /folders/{id}/request-upload | 200 | 403 role_create_forbidden — CREATE | match | Q1 ok, **Q2 mismatch**, Q3 ok, Q4 ok, Q5 n/a | `POST /folders/<id>/request-upload {"path":"ba7489b.txt","size":10}` -> 200 — **F10** |
| vfolder | vfolder | get | create_vfolder_download_session | single_entity/permission | rest-v1:POST /folders/{id}/request-download | 200 | 403 role_create_forbidden | no row (successful read — policy) | Q1 ok, Q2 ok, Q3 n/a, Q4 ok, Q5 n/a | `POST /folders/<id>/request-download {"path":"ba7489b.txt"}` |
| vfolder | vfolder | get | create_vfolder_download_session_v2 | single_entity/permission | rest:POST /v2/vfolders/{id}/download-session | 200 | 403 role_create_forbidden | no row (successful read — policy) | Q1 ok, Q2 ok, Q3 n/a, Q4 ok, Q5 n/a | v2 equivalent of the above |
| vfolder | vfolder | get | create_vfolder_archive_download_session | single_entity/permission | rest-v1:POST /folders/{id}/request-download-archive | 400 api_parsing_invalid-parameters | 403 role_create_forbidden | no row (request rejected at parsing, before the action ran) | Q1 ok, Q2 ok, Q3 n/a, Q4 ok, Q5 n/a | request model differs from the plain download session; not exercised past validation |
| vfolder | vfolder | update | share_vfolder | single_entity/permission | rest-v1:POST /folders/{id}/share | 404 `Only project folders are directly sharable.` | **403 backendai_generic_forbidden — the owner cannot share their own folder** | match (status=error) | Q1 ok, **Q2 mismatch**, Q3 no row, Q4 n/a, Q5 n/a | route carries `admin_required` (`auth.py:887`) though the catalog declares a per-entity permission gate — **F7** |
| vfolder | vfolder | delete | unshare_vfolder | single_entity/permission | rest-v1:POST /folders/{id}/unshare | 404 `Only project folders are directly unsharable.` | 403 backendai_generic_forbidden | match (status=error, operation=delete) | Q1 ok, **Q2 mismatch**, Q3 no row, Q4 n/a, Q5 n/a | same `admin_required` route gate — **F7** |
| vfolder | vfolder | update | update_vfolder_sharing_status | single_entity/permission | rest-v1:POST /folders/_/sharing | 400 api_parsing_invalid-parameters | not reached | no row (request rejected at parsing, before the action ran) | Q1 ok, Q2 n/a, Q3 n/a, Q4 n/a, Q5 n/a | request model not satisfied by `{vfolder_id,status}`; not exercised past validation |
| vfolder | vfolder | search | list_shared_vfolders | single_entity/permission | rest-v1:GET /folders/_/shared | 200 `{"shared": []}` | 200 `{"shared": []}` | no row (successful read — policy) | Q1 ok, Q2 ok, Q3 n/a, Q4 n/a, Q5 n/a | `GET /folders/_/shared` |
| vfolder | vfolder | search | public_list_shared_vfolders | global/public | rest-v1:GET /folders/_/shared | 200 — every share row system-wide | **200 — same, to a caller who is neither owner nor sharee** | no row (successful read — policy) | Q1 ok, **Q2 mismatch**, Q3 n/a, Q4 n/a, Q5 n/a | `GET /folders/_/shared` as monitor@ returns another user's share with their e-mail — **F17** |
| vfolder | vfolder | update | change_vfolder_ownership | single_entity/permission | rest-v1:POST /folders/_/change-ownership | 400 api_parsing_invalid-parameters | 403 backendai_generic_forbidden (superadmin route) | no row (request rejected at parsing, before the action ran) | Q1 ok, Q2 mismatch, Q3 no row, Q4 n/a, Q5 n/a | `superadmin_required` route though the catalog declares a per-entity permission gate |
| vfolder | vfolder | update | update_vfolder_attribute | single_entity/permission | rest-v1:POST /folders/{id}/rename and /update-options | 200 | 403 role_create_forbidden — UPDATE | match | Q1 ok, Q2 ok, Q3 ok, Q4 ok, Q5 n/a | `POST /folders/<id>/rename {"new_name":"ba7489b-q5b-ren"}` as owner -> 200, as user2@ -> 403 |
| vfolder | vfolder | update | update_vfolder_quota | single_entity/permission | rest-v1:POST /folders/_/quota | reached | **400 storage-proxy_request_content-type-mismatch for the owner** | match (status=error) | Q1 ok, Q2 ok, Q3 no row, Q4 mismatch, Q5 n/a | `POST /folders/_/quota {"folder_host":"local:volume1","id":"<own>","input":{"size_bytes":1048576}}` -> 400 — **F16.6** |
| vfolder | vfolder | get | get_vfolder_quota | single_entity/permission | rest-v1:GET /folders/_/quota | 404 vfolder_read_not-found | 400 storage-proxy_request_content-type-mismatch (owner) / 404 (non-owner) | match (status=error — failures are always recorded) | Q1 ok, Q2 ok, Q3 n/a, Q4 mismatch, Q5 n/a | `GET /folders/_/quota?id=<own>&folder_host=local:volume1` -> 400 — **F16.6** |
| vfolder | vfolder | get | get_vfolder_usage | single_entity/permission | rest-v1:GET /folders/_/usage | 404 vfolder_read_not-found | 403 backendai_generic_forbidden (superadmin route) | no row (successful read — policy) | Q1 ok, Q2 mismatch, Q3 n/a, Q4 n/a, Q5 n/a | `GET /folders/_/usage?id=<id>&folder_host=local:volume1` |
| vfolder | vfolder | get | get_vfolder_usage_legacy | single_entity/permission | rest-v1:GET /folders/_/usage | 404 | 403 backendai_generic_forbidden | no row (successful read — policy) | Q1 ok, Q2 mismatch, Q3 n/a, Q4 n/a, Q5 n/a | same route as above |
| vfolder | vfolder | get | get_vfolder_used_bytes | single_entity/permission | rest-v1:GET /folders/_/used-bytes | 404 vfolder_read_not-found | 403 backendai_generic_forbidden (superadmin route) | no row (successful read — policy) | Q1 ok, Q2 mismatch, Q3 n/a, Q4 n/a, Q5 n/a | `GET /folders/_/used-bytes?id=<id>&folder_host=local:volume1` |
| vfolder | vfolder | search | global_list_all_hosts | global/permission | rest-v1:GET /folders/_/all-hosts | 200 `{"default":"local:volume1","allowed":[...]}` | 403 backendai_generic_forbidden | no row (successful read — policy) | Q1 ok, Q2 ok, Q3 n/a, Q4 n/a, Q5 n/a | `GET /folders/_/all-hosts` |
| vfolder | vfolder | search | global_list_allowed_types | global/permission | rest-v1:GET /folders/_/allowed-types | 200 `["group","user"]` | 403 user_auth_forbidden | no row (successful read — policy) | Q1 ok, Q2 ok, Q3 n/a, Q4 n/a, Q5 n/a | `GET /folders/_/allowed-types`; route middleware is `auth_required` but the global processor enforces superadmin |
| vfolder | vfolder | search | global_list_mounts | global/permission | rest-v1:GET /folders/_/mounts | 200 (manager + storage_proxy mounts) | 403 backendai_generic_forbidden | no row (successful read — policy) | Q1 ok, Q2 ok, Q3 n/a, Q4 n/a, Q5 n/a | `GET /folders/_/mounts` |
| vfolder | vfolder | get | global_get_fstab_contents | global/permission | rest-v1:GET /folders/_/fstab | 200 (legacy stub text) | 403 backendai_generic_forbidden | no row (successful read — policy) | Q1 ok, Q2 ok, Q3 n/a, Q4 n/a, Q5 n/a | `GET /folders/_/fstab` |
| vfolder | vfolder | get | global_get_volume_perf_metric | global/permission | rest-v1:GET /folders/_/perf-metric | 400 api_parsing_invalid-parameters (needs a volume argument) | 403 backendai_generic_forbidden | no row | Q1 ok, Q2 ok, Q3 n/a, Q4 n/a, Q5 n/a | `GET /folders/_/perf-metric` |
| vfolder | vfolder | update | global_mount_host | global/permission | rest-v1:POST /folders/_/mounts | **200 while mounting nothing** (no agents registered) | 403 backendai_generic_forbidden | match (`global_mount_host \| global \| update`, status=success) | Q1 ok, Q2 ok, Q3 no row, Q4 n/a, Q5 n/a | `POST /folders/_/mounts {"fs_location":"/tmp/x","name":"ba7489b-mnt","fs_type":"nfs"}` -> 200; mount list unchanged; reverted with `/folders/_/umounts` |
| vfolder | vfolder | update | global_umount_host | global/permission | rest-v1:POST /folders/_/umounts | 200 | 403 backendai_generic_forbidden | match (status=success) | Q1 ok, Q2 ok, Q3 no row, Q4 n/a, Q5 n/a | `POST /folders/_/umounts {"name":"ba7489b-mnt"}` |
| vfolder | vfolder | get | global_batch_load_vfolders | global/permission | gql:node/DataLoader | not exercised directly | not exercised | no row (successful read — policy) | Q1 ok (DataLoader), Q2 n/a, Q3 n/a, Q4 n/a, Q5 n/a | batch-load path behind GraphQL vfolder fields |
| vfolder | vfolder | search | global_search_vfolders | global/permission | cli:vfolder admin-search | ok — returns every user's folders | 403 backendai_generic_forbidden | no row (successful read — policy) | Q1 ok, Q2 ok, Q3 n/a, Q4 n/a, Q5 n/a | `./bai vfolder admin-search --limit 2` |
| vfolder | vfolder | search | list_vfolder | scope/permission | rest-v1:GET /folders | own folders only | own folders only — correct | no row (successful read — policy) | Q1 ok, Q2 ok, Q3 n/a, Q4 n/a, Q5 n/a | `GET /folders` as admin@/user@/user2@ each returned only that caller's rows |
| vfolder | vfolder | search | search_user_vfolders | scope/permission | cli:vfolder my-search | own folders only | own folders only — correct | no row (successful read — policy) | Q1 ok, Q2 ok, Q3 n/a, Q4 n/a, Q5 n/a | `./bai vfolder my-search --limit 10` |
| vfolder | vfolder | search | search_vfolders_in_project | scope/permission | cli:vfolder project-search | ok (empty) | ok (empty) | no row (successful read — policy) | Q1 ok, Q2 ok, Q3 n/a, Q4 n/a, Q5 n/a | `./bai vfolder project-search <proj> --limit 2` |
| vfolder | vfolder | search | search_hosts | scope/permission | rest-v1:GET /folders/_/hosts | 200 with volume_info | 200 with volume_info | no row (successful read — policy) | Q1 ok, Q2 ok, Q3 n/a, Q4 n/a, Q5 n/a | `GET /folders/_/hosts` |
| vfolder | vfolder | get | search_storage_host_permissions | scope/permission | cli:my storage-host permissions | 200 | 200 (same host list and permission set as admin) | match (`vfolder\|get\|scope`) | Q1 ok, Q2 ok, Q3 ok, Q4 n/a, Q5 n/a | `./bai my storage-host permissions` |
| vfolder | vfolder | get | get_task_logs | scope/permission | rest (session task-log route) | not exercised — requires a finished session task log | not exercised | no row | Q1 ok, Q2 n/a, Q3 n/a, Q4 n/a, Q5 n/a | no agent running in this stack, so no session produced a task log |
| vfolder | vfolder | lookup | lookup_vfolder | lookup/permission | none (internal owner resolution) | not exercised | not exercised | no row | Q1 internal-only, Q2 n/a, Q3 n/a, Q4 n/a, Q5 n/a | fires inside the single-entity vfolder actions |
| vfolder | vfolder | lookup | lookup_accessible_vfolder | lookup/permission | rest-v1:GET /folders/{name} (name form) | not exercised separately | not exercised separately | no row | Q1 ok (name-form route), Q2 n/a, Q3 n/a, Q4 n/a, Q5 n/a | `_vfolder_resolver` uses it when the path parameter is a name, not a UUID |
| vfolder | vfolder_invitation | create | invite_vfolder | single_entity/permission | rest-v1:POST /folders/{id}/invite | 201 | **201 — succeeds** | match (`invite_vfolder\|vfolder\|create\|single_entity`) | Q1 ok, Q2 ok, Q3 ok, Q4 n/a, Q5 n/a | gated on the *vfolder*, so the owner may create an invitation nobody can act on — **F6** |
| vfolder | vfolder_invitation | search | list_invitation | scope/permission | rest-v1:GET /folders/invitations/list | 200 | **403 role_create_forbidden — READ at the caller's own user scope** | match (status=denied) | Q1 ok, **Q2 mismatch**, Q3 ok, Q4 n/a, Q5 n/a | `GET /folders/invitations/list` as user@ -> 403; `vfolder_invitation` has **zero** rows in `permissions` — **F6** |
| vfolder | vfolder_invitation | search | list_sent_invitations | scope/permission | rest-v1:GET /folders/invitations/list-sent | 200 | **403 role_create_forbidden — READ at the caller's own user scope** | match (status=denied) | Q1 ok, **Q2 mismatch**, Q3 ok, Q4 n/a, Q5 n/a | `GET /folders/invitations/list-sent` as user@ -> 403; `vfolder_invitation` has **zero** rows in `permissions` — **F6** |
| vfolder | vfolder_invitation | update | accept_invitation | single_entity/permission | rest-v1:POST /folders/invitations/accept | 200 | **403 role_create_forbidden — UPDATE on vfolder_invitation** | match (status=denied) | Q1 ok, **Q2 mismatch**, Q3 ok, Q4 n/a, Q5 n/a | the invitee cannot act on an invitation addressed to them — **F6** |
| vfolder | vfolder_invitation | update | reject_invitation | single_entity/permission | rest-v1:POST /folders/invitations/delete | 200 | **403 role_create_forbidden — UPDATE on vfolder_invitation** | match (status=denied) | Q1 ok, **Q2 mismatch**, Q3 ok, Q4 n/a, Q5 n/a | the invitee cannot act on an invitation addressed to them — **F6** |
| vfolder | vfolder_invitation | update | update_invitation | single_entity/permission | rest-v1:POST /folders/invitations/update/{inv_id} | 200 | **403 role_create_forbidden — UPDATE on vfolder_invitation** | match (status=denied) | Q1 ok, **Q2 mismatch**, Q3 ok, Q4 n/a, Q5 n/a | the invitee cannot act on an invitation addressed to them — **F6** |
| vfolder | vfolder_invitation | purge | leave_invited_vfolder | single_entity/permission | rest-v1:POST /folders/{id}/leave | reached | 403 role_create_forbidden | match (status=denied) | Q1 ok, **Q2 mismatch**, Q3 no row, Q4 n/a, Q5 n/a | same missing-permission root cause — **F6** |
| vfolder | vfolder_invitation | purge | revoke_invited_vfolder | single_entity/permission | rest-v1:POST /folders/invitations/delete | 200 | 403 role_create_forbidden | match (status=denied) | Q1 ok, **Q2 mismatch**, Q3 ok, Q4 n/a, Q5 n/a | same missing-permission root cause — **F6** |
| vfolder | vfolder_invitation | update | update_invited_vfolder_mount_permission | single_entity/permission | rest-v1:POST /folders/_/shared | 200 | **200 `shared vfolder permission updated` for a share that does not exist** | match (status=success) | Q1 ok, Q2 mismatch, Q3 no row, Q4 mismatch, Q5 n/a | `POST /folders/_/shared {"vfolder":"<id>","user":"<u2>","permission":"ro"}` -> 200 though u2 held no share — **F16.5** |
| vfolder | vfolder | delete | bulk delete (adapter loop over delete_vfolder_v2) | single_entity/permission (looped) | cli:vfolder bulk-delete | n/a | **single 403 for the whole batch; the permitted item was still soft-deleted** | one row per processed item | Q1 ok, Q2 ok, Q3 ok, Q4 n/a, **Q5 mismatch** | `./bai vfolder bulk-delete <owned> <other-user's> <miss> <owned-dup>` -> one 403 naming only item 2, yet item 1 became `delete-pending` — **F9** |
| vfolder | vfolder | purge | bulk purge (adapter loop over purge_vfolder_v2) | single_entity/permission (looped) | cli:vfolder bulk-purge | n/a | `{purged_count, failed[]}` — no positional mapping; duplicates counted twice | one row per processed item | Q1 ok, Q2 ok, Q3 ok, Q4 mismatch, **Q5 mismatch** | `./bai vfolder bulk-purge <a> <other's> <miss> <a-dup>` -> `purged_count: 2` for one folder; miss and denial share one message — **F9** |
| container_registry | container_registry | update | handle_harbor_webhook | global/anonymous | rest-v1:POST /container-registries/webhook/harbor | **reached with no credentials at all; manager performed an outbound request to a caller-supplied host** | same — no authentication of any kind | match (`handle_harbor_webhook\|global\|update\|global`, status=error) | **Q1 ok, Q2 mismatch, Q3 mismatch, Q4 n/a, Q5 n/a** | `curl -X POST http://127.0.0.1:8091/container-registries/webhook/harbor -d '{"type":"PUSH_ARTIFACT","event_data":{"repository":{"namespace":"ba7489b","name":"testimg"},"resources":[{"resource_url":"ba7489b.example.com/...","tag":"latest"}]}}'` — **F4** |
| container_registry | container_registry | create | create_container_registry | global/permission | cli:admin container-registry create | ok | 403 backendai_generic_forbidden | mismatch: entity_type=global (catalog container_registry) | Q1 ok, Q2 ok, Q3 mismatch, Q4 n/a, Q5 n/a | `./bai admin container-registry create '{"url":...,"registry_name":"ba7489b-cr",...}'` |
| container_registry | container_registry | update | update_container_registry | global/permission | cli:admin container-registry update / gql:modify_container_registry | ok | 403 backendai_generic_forbidden | mismatch: entity_type=global | Q1 ok, Q2 ok, Q3 mismatch, Q4 n/a, Q5 n/a | PATCH /v2/container-registries |
| container_registry | container_registry | delete | delete_container_registry | global/permission | cli:admin container-registry delete | ok | 403 backendai_generic_forbidden | mismatch: entity_type=global | Q1 ok, Q2 ok, Q3 mismatch, Q4 n/a, Q5 n/a | `./bai admin container-registry delete <id>` |
| container_registry | container_registry | search | search_container_registries | global/permission | cli:admin container-registry search | ok | 403 backendai_generic_forbidden | no row (successful read — policy) | Q1 ok, Q2 ok, Q3 n/a, Q4 n/a, Q5 n/a | `./bai admin container-registry search --limit 3` |
| container_registry | container_registry | get | get_container_registries | global/permission | rest-v1:GET /container-registries | ok | 403 backendai_generic_forbidden | no row (successful read — policy) | Q1 ok, Q2 ok, Q3 n/a, Q4 n/a, Q5 n/a | v1 admin route |
| container_registry | container_registry | get | load_container_registries | global/permission | rest-v1:GET /container-registries/load | ok | 403 backendai_generic_forbidden | no row (successful read — policy) | Q1 ok, Q2 ok, Q3 n/a, Q4 n/a, Q5 n/a | v1 admin route |
| container_registry | container_registry | get | load_all_container_registries | global/permission | gql_legacy (image resolvers) | ok | 403 | no row (successful read — policy) | Q1 ok, Q2 ok, Q3 n/a, Q4 n/a, Q5 n/a | invoked by the legacy image GraphQL resolvers |
| container_registry | container_registry | update | rescan_images | global/permission | gql_legacy:rescan_images / rest-v1:POST /container-registries/rescan | `{ok:true, task_id}` — **bgtask** `rescan_images` | `{ok:false, msg:"no permission to execute rescan_images"}` at HTTP 200 | mismatch: entity_type=global (catalog container_registry) | Q1 ok, **Q2 mismatch**, Q3 mismatch, Q4 n/a, Q5 n/a | `mutation { rescan_images(registry:"cr.backend.ai", project:"stable") { ok msg task_id } }`; denial is a 200 body, not a 403 — **F16.3** |
| container_registry | container_registry | delete | clear_images | global/permission | gql_legacy:clear_images / rest-v1:POST /container-registries/clear | `{ok:true}` | `{ok:false, msg:"no permission to execute clear_images"}` at HTTP 200 | mismatch: entity_type=global | Q1 ok, **Q2 mismatch**, Q3 mismatch, Q4 n/a, Q5 n/a | `mutation { clear_images(registry:"ba7489b-cr") { ok msg } }` — **F16.3** |
| container_registry | container_registry | create | create_registry_quota | global/permission | gql_legacy (harbor quota mutations) | not exercised — requires a live Harbor registry | not exercised | no row | Q1 ok (Harbor-only), Q2 n/a, Q3 n/a, Q4 n/a, Q5 n/a | quota calls proxy to Harbor's own API; no Harbor instance in this stack |
| container_registry | container_registry | get | read_registry_quota | global/permission | gql_legacy (harbor quota mutations) | not exercised — requires a live Harbor registry | not exercised | no row | Q1 ok (Harbor-only), Q2 n/a, Q3 n/a, Q4 n/a, Q5 n/a | quota calls proxy to Harbor's own API; no Harbor instance in this stack |
| container_registry | container_registry | update | update_registry_quota | global/permission | gql_legacy (harbor quota mutations) | not exercised — requires a live Harbor registry | not exercised | no row | Q1 ok (Harbor-only), Q2 n/a, Q3 n/a, Q4 n/a, Q5 n/a | quota calls proxy to Harbor's own API; no Harbor instance in this stack |
| container_registry | container_registry | delete | delete_registry_quota | global/permission | gql_legacy (harbor quota mutations) | not exercised — requires a live Harbor registry | not exercised | no row | Q1 ok (Harbor-only), Q2 n/a, Q3 n/a, Q4 n/a, Q5 n/a | quota calls proxy to Harbor's own API; no Harbor instance in this stack |
| container_registry | image | search | search_images | global/permission | cli:admin image search | ok | 403 backendai_generic_forbidden | no row (successful read — policy) | Q1 ok, Q2 ok, Q3 n/a, Q4 n/a, Q5 n/a | `./bai admin image search --limit 2` |
| container_registry | image | search | search_aliases | global/permission | cli:admin image alias search | ok | 403 backendai_generic_forbidden | no row (successful read — policy) | Q1 ok, Q2 ok, Q3 n/a, Q4 n/a, Q5 n/a | `./bai admin image alias search --limit 3` |
| container_registry | image | create | alias_image_by_id | global/permission | cli:admin image alias create | ok / 404 image_read_not-found on a nonexistent image | 403 backendai_generic_forbidden | mismatch: entity_type=global (catalog image) | Q1 ok, Q2 ok, Q3 mismatch, Q4 mismatch, Q5 n/a | `./bai admin image alias create <image-id> ba7489b-alias1` |
| container_registry | image | create | alias_image | global/permission | gql_legacy:alias_image | `{ok:true}` | 403 / `ok:false` | mismatch: entity_type=global (`alias_image\|global\|create\|global`) | Q1 ok, Q2 ok, Q3 mismatch, Q4 n/a, Q5 n/a | `mutation { alias_image(alias:"ba7489b-legacy-alias", target:"cr.backend.ai/stable/python-torch:1.5-py36-cuda10.1", architecture:"x86_64") { ok msg } }` |
| container_registry | image | delete | dealias_image | global/permission | gql_legacy:dealias_image | `{ok:true}`; 404 image-alias_read_not-found for an unknown alias | 403 / `ok:false` | mismatch: entity_type=global | Q1 ok, Q2 ok, Q3 mismatch, Q4 mismatch, Q5 n/a | `mutation { dealias_image(alias:"ba7489b-legacy-alias") { ok msg } }` |
| container_registry | image | delete | forget_image_by_id | single_entity/permission | cli:admin image forget | ok / 404 on miss | 403 backendai_generic_forbidden | match (`forget_image_by_id\|image\|delete\|single_entity`, entity_id recorded) | Q1 ok, Q2 mismatch, Q3 ok, Q4 mismatch, Q5 n/a | `./bai admin image forget <image-id>` |
| container_registry | image | delete | forget_image | global/permission | gql_legacy:forget_image | reached | 403 / `ok:false` | mismatch: entity_type=global | Q1 ok, Q2 ok, Q3 mismatch, Q4 n/a, Q5 n/a | legacy reference-based variant of the above |
| container_registry | image | purge | purge_image_by_id | single_entity/permission | cli:admin image purge | 404 on miss | 403 backendai_generic_forbidden | match (entity_type=image) | Q1 ok, Q2 mismatch, Q3 ok, Q4 mismatch, Q5 n/a | `./bai admin image purge 000..0ff` |
| container_registry | image | restore | restore_image_by_id | single_entity/permission | rest:POST /v2/images/restore | **404 image_read_not-found — cannot restore a forgotten image** | 403 backendai_generic_forbidden | match (`restore_image_by_id \| image \| restore`, status=error) | Q1 ok, Q2 mismatch, Q3 no row, Q4 n/a, Q5 n/a | forget the image, then `POST /v2/images/restore {"image_id":"<id>"}` -> 404; `ImageRow.get` defaults `filter_by_statuses=[ALIVE]` — **F8** |
| container_registry | image | update | update_image_by_id | global/permission | cli:admin image update | ok | 403 backendai_generic_forbidden | mismatch: entity_type=global | Q1 ok, Q2 ok, Q3 mismatch, Q4 n/a, Q5 n/a | `./bai admin image update '{"image_id":...}'` |
| container_registry | image | update | update_image | global/permission | gql_legacy:modify_image | `{ok:true}` | 403 / `ok:false` | mismatch: entity_type=global (`update_image\|global\|update\|global`) | Q1 ok, Q2 ok, Q3 mismatch, Q4 n/a, Q5 n/a | `mutation { modify_image(target:"cr.backend.ai/stable/python-torch:1.5-py36-cuda10.1", architecture:"x86_64", props:{resource_limits:[]}) { ok msg } }` |
| container_registry | image | create | preload_image | global/permission | gql_legacy:preload_image | **`{ok:false, msg:"Not implemented."}`** | same | no row | **Q1 unreachable**, Q2 n/a, Q3 n/a, Q4 n/a, Q5 n/a | `mutation { preload_image(references:[...], target_agents:["*"]) { ok msg task_id } }` — confirms BA-7486 `W` |
| container_registry | image | delete | unload_image | global/permission | gql_legacy:unload_image | **`{ok:false, msg:"Not implemented."}`** | same | no row | **Q1 unreachable**, Q2 n/a, Q3 n/a, Q4 n/a, Q5 n/a | confirms BA-7486 `W` |
| container_registry | image | purge | purge_images | global/permission | **none** | not exercised — no caller | not exercised | no row | **Q1 unreachable**, Q2 n/a, Q3 n/a, Q4 n/a, Q5 n/a | confirms BA-7486 `W` — no caller; the bgtask uses the singular `purge_image` |
| container_registry | image | update | set_image_resource_limit_by_id | global/permission | **none** | not exercised — no caller | not exercised | no row | **Q1 unreachable**, Q2 n/a, Q3 n/a, Q4 n/a, Q5 n/a | confirms BA-7486 `W` — no caller |
| container_registry | image | delete | clear_image_custom_resource_limit_by_id | global/permission | **none** | not exercised — no caller | not exercised | no row | **Q1 unreachable**, Q2 n/a, Q3 n/a, Q4 n/a, Q5 n/a | confirms BA-7486 `W` — no caller |
| container_registry | image | purge | purge_image | global/permission | bgtask (image purge task) | not exercised directly | n/a | no row | Q1 ok (bgtask-only), Q2 n/a, Q3 n/a, Q4 n/a, Q5 n/a | invoked by the image-purge background task, not by a client route |
| container_registry | image | delete | clear_image_custom_resource_limit | global/permission | gql_legacy:clear_image_custom_resource_limit | reached | 403 / `ok:false` | mismatch: entity_type=global | Q1 ok, Q2 ok, Q3 mismatch, Q4 n/a, Q5 n/a | legacy reference-based variant |
| container_registry | image | delete | untag_image_from_registry | global/permission | gql_legacy:untag_image_from_registry | not exercised — requires a live Harbor registry | 403 / `ok:false` | no row | Q1 ok (Harbor-only), Q2 n/a, Q3 n/a, Q4 n/a, Q5 n/a | calls the registry's own delete API; no Harbor instance in this stack |
| container_registry | image | create | scan_image | global/permission | gql_legacy (single-image scan) | not exercised — outbound registry scan | 403 / `ok:false` | no row | Q1 ok, Q2 n/a, Q3 n/a, Q4 n/a, Q5 n/a | not run to avoid an unnecessary outbound scan of a third-party registry |
| container_registry | image | get | get_image_installed_agents | global/permission | gql_legacy:image.installed_agents | ok (empty — no agents registered) | 403 | no row (successful read — policy) | Q1 ok, Q2 ok, Q3 n/a, Q4 n/a, Q5 n/a | no agent process running in this stack |
| container_registry | image | search | get_all_images | global/permission | gql_legacy:images | ok | 403 (superadmin decorator) | no row (successful read — policy) | Q1 ok, Q2 ok, Q3 n/a, Q4 n/a, Q5 n/a | legacy GraphQL image query surface; superadmin-gated in the resolver |
| container_registry | image | search | get_image_by_id | global/permission | gql_legacy:image_node(id:) | ok | 403 (superadmin decorator) | no row (successful read — policy) | Q1 ok, Q2 ok, Q3 n/a, Q4 n/a, Q5 n/a | legacy GraphQL image query surface; superadmin-gated in the resolver |
| container_registry | image | search | get_image_by_identifier | global/permission | gql_legacy:image(reference:) | ok | 403 (superadmin decorator) | no row (successful read — policy) | Q1 ok, Q2 ok, Q3 n/a, Q4 n/a, Q5 n/a | legacy GraphQL image query surface; superadmin-gated in the resolver |
| container_registry | image | search | get_images_by_canonicals | global/permission | gql_legacy (canonical batch load) | ok | 403 (superadmin decorator) | no row (successful read — policy) | Q1 ok, Q2 ok, Q3 n/a, Q4 n/a, Q5 n/a | legacy GraphQL image query surface; superadmin-gated in the resolver |
