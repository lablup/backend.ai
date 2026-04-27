# Backend.AI Scenario Tests

End-to-end shell scripts that exercise core user journeys via the **`./bai` v2 CLI**
against a live Backend.AI cluster.

These are *integration smoke tests* — they ensure the API surface, CLI plumbing,
permission boundaries, and resource lifecycles all work together. They are not a
substitute for the unit / pytest suite under `tests/`.

## Quick start

```bash
# 1. Cluster up + admin able to log in
./dev start all                      # tmux services
docker compose -f docker-compose.halfstack.current.yml ps   # halfstack healthy

# 2. Run everything (creates test users + projects, runs all 16 scenarios, tears down)
scenarios/run_all.sh

# 3. Only specific scenarios, keep test data afterwards
SKIP_TEARDOWN=1 ONLY="01 02 06" scenarios/run_all.sh
```

## What gets created

`00_setup.sh` provisions, **idempotently**:

| Kind     | Name (default prefix `scn`)            |
|----------|----------------------------------------|
| User     | `scn-userA@scenario.local` (role=user) |
| User     | `scn-userB@scenario.local` (role=user) |
| Project  | `scn-projectA` (domain=default)        |
| Project  | `scn-projectB` (domain=default)        |

User A is added to project A; user B to project B. Resource policies are
`default` for keypair / user / project. Override any of these via env vars
(see `lib/env.sh`).

## Coverage matrix

Last verified: 2026-04-26 against `main` (commit `f55366d34`). 13/17 PASS, 4 FAIL.

| #  | Scenario                     | Domain          | Status  | What it verifies                                                       |
|----|------------------------------|-----------------|---------|------------------------------------------------------------------------|
| 00 | setup                        | -               | ✅ PASS  | admin creates users + projects + memberships, grants vfolder hosts     |
| 01 | vfolder_lifecycle            | vfolder         | ✅ PASS  | create → mkdir → ls → mv → rm → delete → purge                         |
| 02 | session_lifecycle            | session         | ✅ PASS  | enqueue session w/ vfolder mount → wait → terminate → cleanup          |
| 03 | model_card_deploy            | model card      | ❌ FAIL  | model-card project-search → available-presets → deploy → cleanup       |
| 04 | deployment_revision          | model service   | ❌ FAIL  | deployment create → list/current revision → update → delete            |
| 05 | teardown_verification        | session/vf/dep  | ✅ PASS  | no scenario-prefixed leftovers in user A's scope                       |
| 06 | multi_user_access            | vfolder         | ✅ PASS  | user B cannot list or fetch user A's vfolder                           |
| 07 | vfolder_invite_clone         | vfolder         | ❌ FAIL  | cloneable vfolder → clone → both accessible                            |
| 08 | cross_project_isolation      | vfolder         | ✅ PASS  | project-scoped lookups never cross project boundaries                  |
| 09 | vfolder_mounted_delete       | vfolder/session | ✅ PASS  | deleting a vfolder mounted on a live session must be rejected          |
| 10 | vfolder_cloneable_false      | vfolder         | ✅ PASS  | clone of a non-cloneable vfolder must be rejected                      |
| 11 | vfolder_bulk_ops             | vfolder         | ✅ PASS  | bulk-delete + bulk-purge across multiple vfolders                      |
| 12 | vfolder_file_io              | vfolder/storage | ✅ PASS  | TUS upload → ls → download → sha256 round-trip via storage proxy       |
| 13 | session_exec_logs            | session         | ✅ PASS  | BATCH session prints marker, `session logs` retrieves it after exit    |
| 14 | deployment_endpoint_serve    | model service   | ❌ FAIL  | deployment endpoint URL is constructed and L7-reachable                |
| 15 | session_concurrency_cap      | session/policy  | ✅ PASS  | keypair `max_concurrent_sessions=1` rejects the second enqueue         |
| 99 | teardown                     | all             | ✅ PASS  | purges every scenario-prefixed resource and the test users             |

**Pass rate:** 13 / 17 scenarios.

All scenarios are strict — there are no soft-pass / soft-skip paths. A failure here means a real defect or a missing fixture on the cluster.

## Known failures

These scenarios surface real defects (or missing cluster fixtures) that need
upstream attention. They are kept strict so regressions stay visible — do
**not** mask them with `|| true`, `log_warn`, or `soft-pass` style escapes.

| #  | Scenario                  | Symptom                                                                                                                                                                                                                                       | Root cause                                                                                                                                                              |
|----|---------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| 03 | model_card_deploy         | `[FAIL] card has no revision presets` — `model-card project-search` now finds the auto-provisioned card, but `available-presets` returns an empty list.                                                                                       | Two-stage fixture gap. `00_setup.sh` now provisions a model card row (`scn-model-card-fixture`), removing the original "no model cards available" gate. The remaining gap: `deployment_revision_preset` table is empty on a fresh dev DB (verified via `gql { deploymentRevisionPresets }`). Seeding presets requires more than scenario fixtures should do — extend `./scripts/install-dev.sh` to insert at least one preset bound to a runtime variant (`cmd`, `nim`, `sglang`, etc.). |
| 04 | deployment_revision       | After `./bai deployment delete`, `project-search` returns the row with an empty `lifecycle.status` (`NOT TERMINAL: ` — empty string). Scenario expects one of `STOPPED\|DESTROYED\|DELETED\|TERMINATED\|CANCELLED`.                            | Manager bug: soft-delete leaves `lifecycle.status` unset rather than transitioning to a terminal state. The row should report a terminal status synchronously after delete. |
| 07 | vfolder_invite_clone      | `./bai vfolder clone` returns HTTP 403 `PermissionDeniedError: User <uid> lacks permission read on RBACElementRef(VFOLDER, <new_vfolder_id>)` from the post-clone `GET` in `vfolder/adapter.py:626`.                                            | RBAC eventual consistency: the cloned vfolder row is committed, but the owner's `read` permission edge has not been replicated when the immediate post-clone GET runs.   |
| 14 | deployment_endpoint_serve | `[FAIL] no presets available` — same revision-preset gap as 03; this scenario also needs L7-reachable model artifacts on the fixture vfolder once the preset is in place.                                                                       | Same as 03 for the preset gap. Beyond that, the fixture vfolder ships empty — for L7 reachability you also need a real `model-definition.yaml` + weights uploaded to it. Seeding both should live in the dev installer.                                                  |

### Notes for fixers

* **Scenario 03 / 14:** `00_setup.sh` now provisions a fixture vfolder
  (`scn-model-card-fixture`, usage=model) inside the `model-store` project
  and registers it as a model card via `./bai admin model-card create`. With
  that, `model-card project-search` returns the card and 03/14 progress past
  the original "no model cards available" gate. They now stop at the next
  gate — `deployment_revision_preset` rows aren't seeded on a fresh dev DB,
  so `model-card available-presets` returns an empty list. To unblock fully:
    1. Extend `./scripts/install-dev.sh` to insert at least one
       `deployment_revision_preset` row, bound to one of the seeded
       `runtime_variant` rows (`cmd`, `nim`, `sglang`, etc.). Without this
       both 03 and 14 stop at "no presets available."
    2. For 14's L7 reachability: also upload a real `model-definition.yaml`
       and matching weights into the fixture vfolder — the auto-provisioned
       vfolder is empty.
* **Scenario 04:** manager `deployment delete` should transition
  `lifecycle.status` to a terminal state inside the same transaction as the
  row update. The current empty-string state breaks any client that filters
  by status.
* **Scenario 07:** fix manager-side — ensure the new vfolder's owner
  permission edge is visible inside the same transaction as the row insert,
  or retry the post-clone GET until RBAC catches up. A side effect to watch:
  once 07 passes the clone step, the user-side `vfolder delete <clone_id>`
  may still fail with the same `RBACElementRef` error. `99_teardown` cleans
  up via admin context as a fallback so the suite stays idempotent.

## Layout

```
scenarios/
├── README.md
├── lib/
│   ├── env.sh        # endpoints, credentials, resource policy/host names
│   └── common.sh     # logging, login helpers, JSON helpers, retries
├── 00_setup.sh
├── 01_vfolder_lifecycle.sh
├── 02_session_lifecycle.sh
├── 03_model_card_deploy.sh
├── 04_deployment_revision.sh
├── 05_teardown_verification.sh
├── 06_multi_user_access.sh
├── 07_vfolder_invite_clone.sh
├── 08_cross_project_isolation.sh
├── 09_vfolder_mounted_delete.sh
├── 10_vfolder_cloneable_false.sh
├── 11_vfolder_bulk_ops.sh
├── 12_vfolder_file_io.sh
├── 13_session_exec_logs.sh
├── 14_deployment_endpoint_serve.sh
├── 15_session_concurrency_cap.sh
├── 99_teardown.sh
├── run_all.sh
├── .state/           # per-run state (project IDs, session IDs) — gitignored
└── .tmp/             # generated payload JSON, upload artifacts — gitignored
```

## Conventions

* Each script is **self-contained**: sources `lib/env.sh` + `lib/common.sh`,
  configures session endpoint, logs in as the appropriate user, and cleans up
  after itself. Running a single scenario directly is supported.
* Test resources are prefixed with `${SCENARIO_PREFIX}-` (default `scn-`) so
  cleanup is by-prefix and never touches non-scenario data.
* `SCENARIO_DEBUG=1` enables verbose `[DBUG]` output (raw `./bai` invocations
  and parsed JSON snippets).
* **No soft-pass.** If a feature or fixture is unavailable, the scenario
  fails (`exit 1`). Missing fixtures (e.g. no model card on a fresh dev DB)
  must be provisioned, not silently skipped. This is intentional — silent
  skips hide real regressions.

## Environment overrides

```bash
# Different cluster
BAI_ENDPOINT=http://10.0.0.5:8090 scenarios/run_all.sh

# x86_64 host — pick an x86_64 image
TEST_IMAGE_NAME='cr.backend.ai/stable/python:3.12-ubuntu22.04' scenarios/run_all.sh

# Different storage host
TEST_VFOLDER_HOST=local:volume2 scenarios/run_all.sh

# Different test prefix to avoid colliding with another suite run
SCENARIO_PREFIX=ci-$RANDOM scenarios/run_all.sh
```

## Prerequisites

* `./bai` configured for session login against the webserver (`run_all.sh` does this).
* Halfstack up; manager + agent + webserver running.
* At least one image visible to `./bai admin image search` matching `TEST_IMAGE_NAME`.
* At least one healthy agent in the resource group `TEST_RESOURCE_GROUP`.

## Troubleshooting

* **Admin login fails** → check webserver / manager are up (`/halfstack` skill).
* **`image not found`** → run `./backend.ai mgr image rescan cr.backend.ai`.
* **Session never reaches RUNNING** → no agent or insufficient resources;
  the scenario logs the final status and continues to terminate it.
* **`vfolder host not allowed`** → keypair resource policy doesn't permit
  `TEST_VFOLDER_HOST`. Inspect `./bai admin resource-policy keypair search`.
