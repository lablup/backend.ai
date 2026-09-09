# Cluster-network production quality gate

The initial CNI cluster-network release supports Docker agents only. Production promotion requires
the automated checks and a successful two-node privnet run against the exact release commit.

## Required command

```bash
BAI_REQUIRE_DATAPLANE=1 \
BAI_DATAPLANE_RUNTIME=docker \
BAI_DATAPLANE_PRIVNET_MODE=1 \
BAI_DATAPLANE_PRIVNET_SOCKET=/run/backend.ai/privnet/net-privnet.sock \
pants test \
  tests/dataplane/test_cluster_session.py \
  tests/dataplane/test_cross_node.py \
  tests/dataplane/test_cross_node_mtu.py \
  tests/dataplane/test_ipam.py \
  tests/dataplane/test_overlay_isolation.py \
  tests/dataplane/test_encrypted_dataplane.py \
  tests/dataplane/test_agent_restart.py \
  tests/dataplane/test_restart_reachability.py
```

`BAI_REQUIRE_DATAPLANE=1` converts every skip and xfail to a failure. It also requires two distinct
nodes, one distinct agent ID per node, Docker, privnet mode, and a reachable privnet socket from the
agent account on every node.

## Required environment

| Variable | Contract |
|---|---|
| `BAI_DATAPLANE_NODES` | At least two distinct local or SSH node specifications |
| `BAI_DATAPLANE_AGENT_IDS` | One unique manager agent ID per node |
| `BAI_DATAPLANE_MANAGER` | Manager API endpoint for the release candidate |
| `BAI_DATAPLANE_ACCESS_KEY` | Dedicated test keypair access key |
| `BAI_DATAPLANE_SECRET_KEY` | Dedicated test keypair secret key |
| `BAI_DATAPLANE_IMAGE_ID` | Runnable image UUID present on the agents |
| `BAI_DATAPLANE_PROJECT_ID` | Project UUID allowed to use the resource group |
| `BAI_DATAPLANE_ETCD_ADDR` | etcd endpoint used by the release candidate |
| `BAI_DATAPLANE_AGENT_START_CMD` | Command that restarts the agent under its service account |
| `BAI_DATAPLANE_PRIVNET_MODE` | Must be `1` |
| `BAI_DATAPLANE_PRIVNET_SOCKET` | Reachable Unix socket used by the agent |

Pants forwards all `BAI_DATAPLANE_*` variables into its test sandbox. With
`BAI_REQUIRE_DATAPLANE` unset, host-touching tests remain opt-in and missing lab configuration is a
skip.

## Promotion checks

| Area | Required evidence |
|---|---|
| etcd | Real-etcd pagination, compare-and-swap, guard, and lease tests pass |
| Manager HA | One leased reconciliation leader; bounded pages; invalid records preserved and reported |
| Allocation | Subnet, endpoint, and VNI claims remain generation-fenced and converge after retries |
| Scheduler | Session status, history, kernel reset, allocation release, and unbinding commit together |
| Encryption | Cross-node traffic uses the advertised ESP profile; plaintext paths fail closed |
| Lifecycle | Create cancellation, agent restart, teardown, and reused session IDs leave no stale ownership |
| Isolation | Cross-session traffic is blocked and DNS names resolve only within the session |
| Leak guard | Links, veths, routes, firewall rules, XFRM state, mounts, containers, and etcd claims return to baseline |
| Privnet | The agent account can connect; peer UID, protocol version, journal, and socket ownership checks pass |
| Operations | Audit, guarded repair, quarantine, key status, and drained key rotation commands pass |
| Observability | Reconcile failure/staleness, invalid state, unrecoverable state, slowness, and exhaustion rules load |
| Repository | `pants fmt`, `fix`, `lint`, `check`, and `test` pass against `origin/main` |

## Promotion record

Attach the following to the release decision:

- exact commit SHA and Backend.AI version;
- UTC timestamp and node topology;
- Docker, kernel, iproute2, iptables, and privnet unit versions;
- redacted command environment showing every required variable was set;
- complete test output and leak-guard report;
- Prometheus rule validation result;
- BEP-1078 approval reference.

Unit or mocked tests cannot replace this record. A run from an earlier commit does not qualify the
release candidate.

Thirty-fifth round -- the first run against real nodes since `992faf053`, 169 commits ago.

Rig: manager + i-dk-104 at this HEAD, i-dk-112 and i-dk-156 still on `aa2870fd9` (a mixed-version
cluster, which is the shape a rolling upgrade actually has).

**Two blockers had to be cleared before anything could run**, and both would stop a deployment:
the exported venv had pydantic 2.11 while the branch needs >= 2.12 for `pydantic_core.MISSING`
(#14312), so the manager would not import; and the database was 12 migrations behind, so
`enqueue` failed on `column images.customized does not exist`. Neither is network code -- both
come with the branch.

**What worked, first time, on hardware**

- Single-node session: PREPARED -> RUNNING.
- The agent identity record: `caps` carrying backend/vtep_ip/boot_id/updated_at, a `ready` fence
  beside it, and a `boot` key -- the shape the last several rounds built, written correctly.
- The pid-file `flock`: a second agent under one id was refused with `AgentAlreadyRunning`.
- The freshness gate: the two nodes on old code publish no `updated_at`, so the manager refused
  them by name -- "capabilities are dated ...s ago (or never)". Mixed-version admission behaves
  as designed, and the message says which node and why.

**A11l -- what only hardware could find, and it was mine**

Routing REPLACE to `expired` -- back to PENDING to be scheduled elsewhere -- is unbounded BY
CONSTRUCTION, and the branch's own unit tests could not see it. The retry budget is read from
`last_phase`, which `_carry_last_phase` attaches only while the session's most recent history
record is still the same phase; a round trip through PENDING puts `schedule-sessions`,
`check-precondition` and `promote-to-prepared` in between, so `last_phase` comes back None, every
attempt starts at 1, and the budget never binds.

Measured: 31 full scheduling cycles in four minutes, 128 history rows, no end. Before the change
the same failure took five attempts in place and terminated with a reason the user could read.
I had traded a bounded failure for a livelock.

REPLACE now falls through to the ordinary classification. Same rig, same refusing node: one
merged `start-sessions` row reaching `attempts=5`, then TERMINATING, then TERMINATED -- 7 history
rows against 128. The refusing agents are still recorded against the session, so a later
scheduling round avoids them; re-placement done properly needs a bound that survives the round
trip, and that is a durable per-session counter this branch should not be inventing.

`SCENARIOS.md` is not updated: what ran here is not the release gate. P2 (two-node connectivity),
P4 (MTU), P5 (isolation) and the encryption-wire checks need two nodes on the SAME code, and two
of the three are 169 commits behind.
