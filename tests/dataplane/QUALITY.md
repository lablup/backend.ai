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

Verified at `25bcca215`. Every C and D item below has the named test, and each one was seen to
fail against the code as it stood before the fix.

| # | Was | Now |
|---|-----|-----|
| C1 | two concurrent creates of one session claimed two subnets; the one no meta named leaked | one subnet, one VNI, one address; both callers get the same |
| C2 | met | met |
| C3 | a create killed between the two writes left an address with no endpoint record | the record is written whether the call made the claim or found it |
| C4 | a half-failed rollback left a meta naming resources the pool had freed | the allocation is kept when the record cannot be cleared, and a record whose allocation moved on is not reused |
| C5 | met | met |
| C6 | met, unguarded | guarded by `TestAllocationRoundTrips` |
| D1 | default route, bridge MTU, gateway address, MASQUERADE, FORWARD accept and `route_localnet` all ran unchecked | checked; probes and best-effort deletes stay unchecked |
| D2 | `except Exception` let a cancelled setup leave a VXLAN device behind, and the forward-accept rules sat outside every rollback scope | one scope over the whole of setup, `BaseException`, undone under a shield |
| D3 | the privnet dropped the plan before the detach it describes; a failed one left nothing to retry with, and teardown walked past it | the plan goes once the detach has happened, and a stuck one raises `OverlayTeardownIncomplete` |
| D4 | the preflight downed every tunnel on the node, another agent's included | a VNI the registry attributes to another agent that is still running containers on it is left alone |
| D5 | met | met |

R1 met (`# noqa` and `# type: ignore` both absent from the feature). R2 met: the BEP now says
privnet delegation is opt-in and that Docker is the runtime wired today.

R3, on the three-node rig, at `b86473af9`: G20-G24 encrypted 6/6, G15/G16 overlay isolation 2/2,
G17 IPAM, G14 cross-node, G17/G18 MTU 2/2, plus 101 harness and driver tests. The privnet
orphan-recovery fix was watched live -- the node came back 45s after the cause went, where the
same condition had previously left it out of service indefinitely.

Two things this run did NOT establish, and neither should be read as met:

- **G10/G11/G12 do not exercise this branch's LOCAL data plane.** A SINGLE_NODE session with more
  than one kernel gets `bai-singlenode-<session>`, a Docker network (`launcher.py`), and no
  `bailo*` device exists while they run -- measured, not inferred. They are regression cover for
  the path Backend.AI already had. G12 fails there roughly two runs in three; that is worth its
  own investigation and it is not about the code reviewed here. Cross-session isolation on our
  own data plane is G15/G16, which pass.
- **A1/A2/A3/A9/A10 (agent restart) still have not run.** They were failing on a misconfigured RPC
  port, and with that corrected the node does not come back from the harness stop/start cycle.
  Rig plumbing, but unproven either way, so D2 and D4 rest on unit evidence across a restart.
