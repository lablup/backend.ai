# Quality bar for the runtime-neutral cluster network

What this feature must guarantee before it is enabled anywhere real, and how each guarantee is
checked. A line here is not a wish: it names the property, the way it fails, and the test that
would catch the failure. An item with no executable check is not met.

The scenario ids (`G*`, `A*`) are the ones in `SCENARIOS.md`.

## C — Control plane (manager)

| # | Property | Fails as | Check |
|---|----------|----------|-------|
| C1 | **One allocation per session, however many callers.** N concurrent `create_network` for one session id yield one subnet, one VNI, one address per container. | Two managers each claim a block; only the last reaches the meta, so the other leaks for the cluster's lifetime. | `TestTwoManagersCreatingOneSession` |
| C2 | **A create that does not finish claims nothing.** Exception, `CancelledError`, or process death leaves either nothing claimed, or only claims a retry provably reuses. | A cancelled launcher call strands a subnet and a VNI. | `TestACreateThatNeverFinished` |
| C3 | **An address implies an endpoint record.** Whatever order the writes land in, a container that holds an IP appears in `endpoints/`. | Session runs; peers never program FDB/ARP for it, so cross-node traffic to that kernel is black-holed while everything reports healthy. | `TestAnAddressWithNoEndpointRecord` |
| C4 | **Meta never outlives what it names.** The session's meta and its subnet/VNI claims are released together, or neither is. | Rollback half-fails; the meta survives pointing at a VNI another session now owns, and the next retry hands out a stranger's data plane. | `TestAMetaThatOutlivedItsAllocation` |
| C5 | **A claim is released only by its owner.** | One session's teardown frees the block a later session is using. | `TestAllocationOwnership` |
| C6 | **Allocation cost does not grow with the pool.** Claiming the Nth session is O(1) round trips, not O(N). | A cluster with a few hundred sessions spends minutes in etcd per launch. | `TestAllocationRoundTrips` |

## D — Data plane (agent)

| # | Property | Fails as | Check |
|---|----------|----------|-------|
| D1 | **A command that establishes required state is checked.** Probes and best-effort deletes may be unchecked; anything the session depends on may not be. | A container comes up with no default route, no MTU, or no MASQ rule, and the session is reported RUNNING. | `TestEveryRequiredCommandIsChecked` |
| D2 | **Setup is all-or-nothing on the host.** A setup that raises *or is cancelled* leaves no bridge, VXLAN device, XFRM state, veth or rule behind. | A cancelled launch strands a VXLAN device; the next session drawing that VNI inherits it. | `TestASetupThatWasCancelled`, G19 |
| D3 | **Teardown reports, and keeps what a retry needs.** A detach that failed says so, and the plan naming the leftovers survives until the detach actually happens. | Teardown returns success over a veth and an address that are still allocated. | `TestADetachThatDidNotGoThrough`, `TestADetachWhosePlanMustSurvive` |
| D4 | **An agent touches only what it owns.** On a host running two agents, one's recovery does not disturb the other's devices. | Restarting agent A drops agent B's session traffic. | G24, A7 |
| D5 | **The overlay is encrypted, or the session does not start.** Under the default policy a node that cannot do the profile is refused, not silently downgraded. | Cluster traffic crosses the wire in clear text. | G20, G21 |

## R — Release quality

| # | Property | Check |
|---|----------|-------|
| R1 | No suppressed lint or type errors anywhere in the feature. | `grep` for `# noqa` / `# type: ignore`; `pants lint check` |
| R2 | Docs and config descriptions state the shipped default, not the intended one. | Read against `config/unified.py` |
| R3 | The scenarios backing every claim above actually execute against real nodes. | `SCENARIOS.md` status column, and the run log |

## Status

Filled in by the verification pass; `SCENARIOS.md` carries the per-scenario record.
