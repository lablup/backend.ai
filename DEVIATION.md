# Deviation Report: BA-5499

| Item | Type | Reason / Alternative |
|------|------|----------------------|
| Task 4: Live verification | Not implemented | Live verification requires stopping running coordinator processes (PIDs 1781, 1840, 97543, 97609), creating inference endpoints with ML models, and scaling services. Automated execution risks disrupting the user's active environment (3 running kernel containers, 2 coordinator instances). This is manual QA — the code changes are verified by unit tests (4/4 pass), type checking (mypy clean), and lint (all pass). |

## Manual Verification Steps

To verify the fix manually:

1. Stop existing coordinators and restart from `worktrees/BA-5499/`
2. Clean etcd traefik keys: `docker exec backendai-backendai-half-etcd-1 etcdctl --endpoints=127.0.0.1:2379 del --prefix "traefik/worker_worker-1"`
3. Initialize rootKey: `docker exec backendai-backendai-half-etcd-1 etcdctl --endpoints=127.0.0.1:2379 put "traefik/worker_worker-1" ""`
4. Create two inference endpoints, scale one 1→2→1
5. Verify etcd has no stale session keys after scale-in
6. Check coordinator logs for:
   - `"Circuit {id} was deleted, skipping route propagation"` (deletion path)
   - `"Re-read circuit {id} from DB for route propagation"` (fresh read path)
   - Lock acquisition around `update_circuit_routes()` and `unload_circuits()`
