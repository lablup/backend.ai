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
| C5 | **A claim is released only by its owner.** Including between two creates of the *same* session: they share the allocation, so only the one that owns the session record may undo. | One session's teardown frees the block a later session is using; or a create that failed beside one that succeeded releases what the successful one already handed to its agents. | `TestAllocationOwnership`, `TestACreateThatFailedBesideOneThatDidNot` |
| C7 | **A block counts as held only when every unit of it is.** | A `/23` whose second half nothing holds is handed back as complete, and the pool gives that half to the next session. | `TestABlockClaimedOnlyInPart` |
| C6 | **Allocation cost does not grow with the pool.** Claiming the Nth session is O(1) round trips, not O(N). | A cluster with a few hundred sessions spends minutes in etcd per launch. | `TestAllocationRoundTrips` |
| C8 | **One incarnation's cleanup never reaches another's.** A session id is reused; every key and claim carries the incarnation that wrote it, and each delete names one. | A cleanup paused between its tombstone check and its delete resumes into the session that replaced the one it came for, and gives that session's VNI back to the pool. | `TestACleanupPausedBetweenItsCheckAndItsDelete`, `TestAnAllocationReusedWhileItIsBeingDestroyed` |
| C9 | **A node is in the session, or it never builds.** Membership is published before any device exists, and the teardown reads the table again after fencing the record. | The manager sees an empty table, hands the VNI to the next session, and only then does a joining node create a tunnel on it. | `TestANodeThatJoinsAsTheRecordIsFenced`, `TestJoiningBeforeBuilding` |
| C10 | **A request acts only on the session it was issued for.** The descriptor an agent is handed is compared against the manager's record, incarnation first. | A launch RPC delayed across a teardown and a rebuild builds the old data plane and publishes the node as a member of the new session. | `TestARequestThatArrivedTooLate` |
| C11 | **Nothing an earlier incarnation writes lands in a later one.** Endpoint, address and membership writes are compare-and-swaps that refuse another incarnation's bytes; a create that finds the record gone gives back what its own incarnation still holds. | A create stalled past the handover resumes into the live session: its addresses go under the live container ids, every peer programs them, and its rollback -- finding the record is not its -- cleans up nothing. | `TestACreateThatWokeUpInAnotherSession`, `TestAnEarlierInstanceStillRunning` |
| C12 | **A table shared with another incarnation is read as one.** Endpoints and members carrying a different generation are not programmed. | A leftover record points this node's FDB and ARP at an address the live session's kernels do not hold, and the frames leave with nothing answering. | `TestATableSharedWithAnotherIncarnation` |

## D — Data plane (agent)

| # | Property | Fails as | Check |
|---|----------|----------|-------|
| D1 | **A command that establishes required state is checked.** Probes and best-effort deletes may be unchecked; anything the session depends on may not be. | A container comes up with no default route, no MTU, or no MASQ rule, and the session is reported RUNNING. | `TestEveryRequiredCommandIsChecked` |
| D2 | **Setup is all-or-nothing on the host.** A setup that raises *or is cancelled* leaves no bridge, VXLAN device, XFRM state, veth or rule behind. | A cancelled launch strands a VXLAN device; the next session drawing that VNI inherits it. | `TestASetupThatWasCancelled`, G19 |
| D3 | **Teardown reports, and keeps what a retry needs.** A detach that failed says so, and the plan naming the leftovers survives until the detach actually happens. | Teardown returns success over a veth and an address that are still allocated. | `TestADetachThatDidNotGoThrough`, `TestADetachWhosePlanMustSurvive` |
| D4 | **An agent touches only what it owns.** On a host running two agents, one's recovery does not disturb the other's devices. | Restarting agent A drops agent B's session traffic. | G24, A7 |
| D6 | **What reaches the manager names the failure.** A node whose privileged helper is down says so, with the socket and what it means. | An operator sees errno 111 and cannot tell which node, or that its whole data plane is down. | `TestWhatReachesTheManagerWhenThePrivnetIsDown` |
| D5 | **The overlay is encrypted, or the session does not start.** Under the default policy a node that cannot do the profile is refused, not silently downgraded. | Cluster traffic crosses the wire in clear text. | G20, G21 |
| D7 | **Recovery's rule listing is an answer or an error, never an empty host.** Only `rc == 0` says what a previous life left. | A missing binary or a denied exec reads as "no rules", and the node is reported ready over a plaintext-drop the next session given that VNI runs into. | `TestACommandThatNeverReturns` |
| D8 | **The privnet acts only for the incarnation it holds.** Every session-scoped request names one, and the VNI binding is made under it. | The lock orders requests per session id but cannot say whose they are: a delayed TEARDOWN deletes the data plane of the session that replaced the one it was issued for. | `TestARequestForAnotherIncarnation` |
| D9 | **A host check that could not run is not a host with nothing on it.** The FORWARD-ACCEPT probe skips only on a missing binary; the address inventory refuses the allocation rather than returning empty. | A denied exec leaves the overlay unprotected on a DROP-policy node, or hands out the block a leaked bridge is already on -- two gateways for one subnet. | `TestBlocksAlreadyOnTheHost`, `_ensure_forward_accept` |

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
| D4 | the preflight downed every tunnel on the node, another agent's included | a VNI whose binding is *built*, whose owner is another agent, and whose owner is running a container of that session, is left alone -- matching on the session alone let a dead agent's reservation except an unverified tunnel |
| D5 | met | met |
| D6 | a bare `RuntimeError` carrying errno 111 | `PrivilegedNetworkHelperUnreachable`, with the socket and an error code |

Second round, against the same bar:

| # | Was | Now |
|---|-----|-----|
| C5 | two creates of one session share the allocation, and the one that failed released what the one that succeeded had already handed to its agents -- deleting its meta and endpoint with it | the session is claimed before anything is claimed for it; only the owner of that record allocates or undoes, and a loser waits for the winner rather than building alongside it |
| C7 | `_already_held` answered on one unit of a wide block | every unit, and a partial claim is finished or given back |
| D2 | the container attach caught `Exception`, so a cancelled one left applied interfaces, a veth and a lease with nothing naming them | `BaseException`, shielded, each DEL reported; and the failure carries the plan so the leftovers have a name to be torn down by |

R1 met (`# noqa` and `# type: ignore` both absent from the feature). R2 met: the BEP now says
privnet delegation is opt-in and that Docker is the runtime wired today.

R3, on the three-node rig, at `992faf053`: G20-G24 encrypted 6/6, G15/G16 2/2, G10-G13 session
isolation 4/4, G17 IPAM, G14 cross-node, G17/G18 MTU 2/2, A11 orphan reap, plus 101 harness and
driver tests. Earlier, at `b86473af9`: G20-G24 encrypted 6/6, G15/G16 overlay isolation 2/2,
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
- **G9 (a 3-kernel single-node cluster session) fails on this rig.** `tenacity.TryAgain` out of
  the container-startup wait -- no network command failed. It fails identically at `de4f1167b`,
  before any of this, so it is not the quality work; it is the single-node startup flake this
  branch inherited, at the heaviest single-node shape.
- **A1/A2/A3/A9/A10 (agent restart) still have not run.** They were failing on a misconfigured RPC
  port, and with that corrected the node does not come back from the harness stop/start cycle.
  Rig plumbing, but unproven either way, so D2 and D4 rest on unit evidence across a restart.

Third round, against the same bar:

| # | Was | Now |
|---|-----|-----|
| C4 | the cleanup checked it still held the tombstone and then deleted a whole prefix; between the two the record could be taken, the cleanup finished by somebody else and a new session built, and the deletes landed on that session | every key and pool claim carries the incarnation that wrote it, and each delete names its own -- the check is an early-out, not the fence |
| C4 | a create that found a READY record checked the pool and then handed the allocation back with no last word on the record | the record is compared again, byte for byte, before anything is returned |
| C9 | the node built its data plane and published its membership after; the manager read the table once, before fencing the record, so neither saw the other | membership goes first, and the teardown reads the table again with the tombstone already in -- there is no order in which a node is missed by both |
| C10 | `READY` was the whole fence, and it says nothing about WHICH incarnation of a reused session id the record is | the descriptor's generation, subnet, VNI, port and key are compared against the record; a withdrawal names the bytes the join wrote |
| D7 | the recovery inventory read every `OSError` as a host with no firewall | only `rc == 0` is an answer; anything else is owed, and `_sweep_orphan_rules` records the debt |

R3 has NOT been re-run for this round: the hardware evidence above is still at `992faf053`, which
predates it. C8-C10 and D7 rest on unit evidence alone, and the agent-restart scenarios
(A1/A2/A3/A9/A10) that would exercise the join/teardown ordering on real nodes remain unrun. Read
the round as unverified against hardware until that log is replaced.

Fourth round, against the same bar:

| # | Was | Now |
|---|-----|-----|
| C11 | a create stalled past the handover wrote its endpoint record unconditionally, so its addresses landed under the live session's container ids; and its rollback, finding the record was not its, returned having cleaned up nothing | the endpoint write is a compare-and-swap that refuses another incarnation's bytes, and a rollback whose record has moved on gives back what its own incarnation still holds |
| C11 | the join wrote this node's member key unconditionally and then deleted exactly those bytes -- so an earlier agent instance clobbered a later one's membership and then removed it, leaving a live data plane with none | the publish refuses another incarnation and replaces its own by compare-and-swap; the withdrawal deletes the bytes it read, not the key |
| C12 | endpoints and members were read whole, whichever incarnation wrote them | a record of another incarnation is not programmed, and does not answer as a cluster name |
| C4 | the agent's single-node meta deletion read the record and then deleted the key | it deletes the bytes it read, so a manager record published under the id in between survives |
| D8 | the privnet identified a session by its id alone, in the RPC, in its journal, in `_SessionEntry` and in the VNI binding digest | every session-scoped request names its incarnation, the privnet refuses one it does not hold, and the digest tells two incarnations on the same subnet and VNI apart |
| D9 | any `OSError` from the FORWARD-ACCEPT probe read as "no iptables here", and an unreadable address inventory read as "this host carries nothing" | only a missing binary skips the probe; an inventory that cannot answer refuses the allocation |
