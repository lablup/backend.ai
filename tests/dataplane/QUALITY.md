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
| C13 | **A pool claim is owned by an incarnation, not a session id.** Adoption, partial-claim completion and release all match on both. | A later incarnation adopts a stalled one's block; the stalled one's cleanup gives it back, and the pool hands it to a third session while the live one is on it -- two tenants at one address range. | `TestASubnetTwoIncarnationsBothClaim` |
| C14 | **A child key is created under the record that makes it legitimate, in one store operation.** Endpoint, address and member writes name the session record as a guard. | A stamp says whose a key is but cannot stop one being MADE: a stale create finds the address free (because the session was torn down) and attaches its state to a session that no longer exists. | `TestAChildKeyWrittenUnderNoRecord` |
| C16 | **A guard is wired into the path that needs it.** The create, the reuse and the pre-seed pass the session record; the pool claims do too. | A guard that exists on the allocator and is not passed by its caller protects nothing, and a test that supplies its own guard passes over the gap. | `TestTheGuardIsWiredIntoTheRealPath` |
| C17 | **One agent id, one agent process.** The pid file is held under an exclusive lock. | Two agents under one id are one identity to the manager, the VNI registry and the privnet journal; no session-level fence separates them, so a restart's outgoing process can withdraw the incoming one's membership. | `_hold_pid_file` |
| C18 | **A lost claim is one candidate; an expired guard is all of them.** Both allocators tell the two apart at the first miss. | Read as a conflict, an expired guard walks the whole VNI range -- ~16.7M swaps and prefix reads -- holding the manager and its etcd for as long as that takes. | `TestAGuardThatExpiredMidScan` |
| C19 | **A claim from before the field is taken, not shared.** A legacy subnet or VNI is promoted to the adopting incarnation before it is used, all units or none. | Two incarnations read one claim as theirs: the newer runs on it, the older's cleanup gives it back, and the pool hands a live session's VNI or half its subnet to another tenant. | `TestALegacyClaimTwoIncarnationsCanRead`, `TestAWideBlockOnTwoIncarnations` |
| C24 | **A promotion touches only a claim that is still this session's.** Every unit is checked to be this session's claim on this block before it is rewritten. | A promotion driven from a RECORD has no claim in front of it, and a compare-and-swap naming "whatever bytes are there" rewrites another session's claim into this one's -- two sessions then believe they own one subnet. | `test_promotion_does_not_take_a_block_another_session_now_holds` |
| C25 | **A reuse that cannot take its allocation hands back nothing.** | Warning and continuing builds a data plane on a subnet or VNI this session does not hold, or on one an earlier cleanup can still give away. | `test_a_reuse_that_cannot_take_its_allocation_hands_back_nothing` |
| C26 | **Compatible is not in use.** An unstamped claim counts as live only where the record names that very subnet or VNI. | Anything else under the id is read as live forever: promotion follows the record and never reaches it, and the sweep skips it. | `test_an_extra_unstamped_claim_of_a_live_session_is_reclaimed` |
| C23 | **A live unstamped claim is TAKEN, not merely preserved.** The startup sweep and the reuse path stamp it with the incarnation its record names; a cleanup for an incarnation the record has moved on from will not take an unstamped claim. | Unstamped is compatible with every incarnation, so between "preserved" and "promoted" any earlier cleanup gives a running session's subnet and VNI back to the pool. | `test_the_sweep_takes_a_preserved_legacy_claim_rather_than_leaving_it`, `test_an_earlier_cleanup_does_not_take_a_live_unstamped_claim` |
| C22 | **An unstamped claim is compatible, not garbage.** The reconciler judges by `of_generation`, the same rule the allocators use. | Comparing the two generations directly makes every claim carried over an upgrade a mismatch -- so the first start of the manager that upgraded them deletes the live subnet and VNI of every such session. | `test_a_live_sessions_legacy_subnet_survives_the_sweep` |
| C21 | **A judgement and the delete it justifies are one operation.** The reconciler carries the record state it judged on into the delete as a guard. | It reads a claim, finds no session, and deletes -- while in between the session is rebuilt over that very unit. A re-read before the delete conditions it on the claim the sweep never judged, and takes a live tenant's subnet. | `test_a_claim_retaken_between_the_judgement_and_the_delete_survives` |
| C20 | **The pool itself is reconcilable.** A sweep starts from the claims and asks each session, so it reaches what no record, tombstone or debt note names. | The one leak nothing can find: a cleanup whose debt write AND release both failed. | `TestAPoolClaimNothingNames` |
| C15 | **A cleanup that cannot finish is written down and retried.** The orphan sweep records what it owes per incarnation and clears it only when nothing is left. | The sweep has no tombstone to work from -- the record already names its successor -- so one transient etcd error leaks a VNI, a subnet and their keys for the cluster's life. | `TestACleanupThatCouldNotFinishIsRetried` |

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
| D9 | **A host check that could not run is not a host with nothing on it.** Neither the FORWARD-ACCEPT probe nor the address inventory reports a failure as an empty host. | A denied exec leaves the overlay unprotected on a DROP-policy node, or hands out the block a leaked bridge is already on -- two gateways for one subnet. | `TestForwardAccept`, `TestBlocksAlreadyOnTheHost` |
| D10 | **A request reaches the privnet through the client its session is bound on, and an unfenced daemon takes no overlay session.** The port forwarder shares the session network's client; the fence is a protocol version, and readiness blocks on it. | A second client on the same socket sends unstamped requests the privnet cannot tell from a stale one's; and a daemon older than the fence carries out a teardown issued for a session that no longer exists. | `TestARequestForAnotherIncarnation`, `_port_publisher` |

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

Fifth round is below; fourth round, against the same bar:

| # | Was | Now |
|---|-----|-----|
| C11 | a create stalled past the handover wrote its endpoint record unconditionally, so its addresses landed under the live session's container ids; and its rollback, finding the record was not its, returned having cleaned up nothing | the endpoint write is a compare-and-swap that refuses another incarnation's bytes, and a rollback whose record has moved on gives back what its own incarnation still holds |
| C11 | the join wrote this node's member key unconditionally and then deleted exactly those bytes -- so an earlier agent instance clobbered a later one's membership and then removed it, leaving a live data plane with none | the publish refuses another incarnation and replaces its own by compare-and-swap; the withdrawal deletes the bytes it read, not the key |
| C12 | endpoints and members were read whole, whichever incarnation wrote them | a record of another incarnation is not programmed, and does not answer as a cluster name |
| C4 | the agent's single-node meta deletion read the record and then deleted the key | it deletes the bytes it read, so a manager record published under the id in between survives |
| D8 | the privnet identified a session by its id alone, in the RPC, in its journal, in `_SessionEntry` and in the VNI binding digest | every session-scoped request names its incarnation, the privnet refuses one it does not hold, and the digest tells two incarnations on the same subnet and VNI apart |
| D9 | any `OSError` from the FORWARD-ACCEPT probe read as "no iptables here", and an unreadable address inventory read as "this host carries nothing" | only a missing binary skips the probe; an inventory that cannot answer refuses the allocation |


Fifth round, against the same bar:

| # | Was | Now |
|---|-----|-----|
| C13 | `_claimed_subnet` matched the session id alone, so a later incarnation adopted a stalled one's block -- and the stalled one's release then handed a live session's subnet back to the pool | ownership is (session, incarnation) through adoption, partial-claim completion and release; a claim from before the field is still adopted, and a retry of one incarnation still converges |
| C14 | endpoint, address and member writes were compare-and-swaps on their own key, which still CREATES it when absent -- and absent is what a teardown had just made it | each is one store operation naming the session's record as a guard, so it lands under the session it is for or not at all |
| C15 | the orphan sweep logged its failures and returned; nothing named what it had not given back | it writes the debt down per incarnation and the next create or teardown of that id pays it |
| D10 | the Docker port publisher built its own privnet client, which carried no incarnation at all | it shares the session network's bound client, and a client is refused the port path if there is none |
| D10 | the incarnation was an optional field a daemon on protocol 3 ignored, and a new daemon accepted unstamped requests for a session it held an incarnation for | protocol 4, readiness blocks a node whose helper is older, and what is fenced is decided by what the node holds rather than by what the request carries |
| D9 | a missing iptables binary skipped the FORWARD-ACCEPT probe, though this backend already declares iptables required | the probe refuses; a readiness failure is no longer laundered into a session that comes up carrying nothing |

R3 is still not re-run: the hardware evidence remains at `992faf053`, which predates all three of
these rounds. Nothing in C8-C15 or D7-D10 has been exercised on real nodes, and the agent-restart
scenarios (A1/A2/A3/A9/A10) that would cover overlapping restarts are still unrun. One risk this
round adds is not covered by any unit test either: `HostAddressesUnreadable` and the FORWARD-ACCEPT
refusal are new ways for a node to stop taking sessions, and only a real node shows how often they
fire.

Known and NOT addressed: two agent processes sharing one agent id and one incarnation are not told
apart -- there is no process-incarnation token below the session generation. It is out of reach of
this fencing scheme, which is per session, and is a misconfiguration rather than a race, but a node
running two agents under one id can still have one withdraw the other's membership.


Sixth round, against the same bar:

| # | Was | Now |
|---|-----|-----|
| C16 | `EndpointAllocator.assign` grew a `guards` parameter and NOT ONE of its three call sites passed it -- an editing script raised partway and wrote nothing, and the round's own test supplied its own guard, so it passed over the gap | the create, the reuse and the pre-seed all pass the record they hold, and the test asserts it through `create_network` rather than through the allocator |
| C13 | pool claims were made with no guard at all, so a create stalled past the handover could claim a subnet and a VNI on behalf of a session that had moved on -- and be killed before publishing, leaving them named by no meta, no tombstone and no debt | the unit and VNI claims are guarded on the session record in the same store operation |
| C13 | an unstamped claim was adoptable by every incarnation at once and was never rewritten, so two of them read one claim as theirs | adoption promotes the claim to the adopting incarnation by value-CAS, in place; a promotion that loses falls back to a block of its own |
| C15 | a debt that could not be written was logged and the sweep continued; a debt that could not be READ let the create carry on | both are consequential: the read raises so the caller retries, and a sweep that fails with no note behind it is reported as unrecoverable |
| C17 | the pid file was written and closed, so nothing stopped a second agent under one id | held under `flock` for the life of the process; the second refuses to start |

R3 remains un-run against the current HEAD. Nothing in C8-C18 or D7-D10 has been exercised on real
nodes, and A1/A2/A3/A9/A10 are still unrun -- which matters more this round than last, because C17
changes agent STARTUP: a node whose pid file is held by a stale process now refuses to start where
it previously started and raced. That is the intended behaviour and it is exactly the kind of
change only a real restart shows.


Seventh round, against the same bar:

| # | Was | Now |
|---|-----|-----|
| C18 | a lost compare-and-swap was always read as "that candidate was taken", so an expired session guard made every candidate lose in turn -- the VNI range is 4096..16,777,215 | the guard is re-read at the first miss and the scan stops with `SessionRecordContested`; an ordinary conflict still moves to the next candidate |
| C19 | `_own_vni` returned a legacy claim as this incarnation's without promoting it, so the claim still answered to any incarnation that asked | promoted by a guarded value-CAS before it is returned; a promotion that cannot land does not hand the claim back |
| C19 | `_claim_as_ours` rewrote a wide block unit by unit with no guard and no rollback, and `_finish_partial_claim` completed a block leaving its older units unstamped | promotion is guarded and all-or-nothing (units already rewritten are put back), and a completed partial claim is brought onto one incarnation or given back |
| C20 | a sweep whose debt note and release both failed left claims nothing named, and nothing would ever look for them | `reconcile_pool` walks the pool and asks each session's record; it runs at manager start, and what could not be recorded is reported through `unrecoverable_leaks` |

R3 is STILL not run against the current HEAD, and this round widens what that leaves unverified
rather than narrowing it. `reconcile_pool` runs at every manager start and releases pool claims
whose session does not name their incarnation -- correct by the model, and a release of live
tenant state if the model is wrong anywhere. Nothing but a real multi-node run with restarts shows
that. Read C18-C20 as reasoned and unit-tested, not as verified.


Eighth round, against the same bar:

| # | Was | Now |
|---|-----|-----|
| C21 | the reconciler judged a claim an orphan, then RE-READ the claim and deleted whatever it found -- so a unit released and re-taken between the two was deleted out from under the session that had just taken it. Worse than the leak it replaced: it deletes live state, and it runs at every manager start, so a rolling restart is where it would show | the bytes it judged on come back with the judgement, and the record that made the claim garbage is carried into the delete as a guard (`compare_and_delete`, where a guard of None means "still absent"). Judgement and delete are one store operation |
| C19 | the VNI lost-CAS re-lookup returned `_own_vni` straight, skipping the promotion the first lookup does -- and that is the path a rolling upgrade takes, where an older manager writes the unstamped claims | both lookups go through `_adopt`, which promotes or declines |
| C20 | the reconciler gave back subnets and VNIs only; a failed sweep's endpoint, member and address keys stayed, and a member key that outlives its incarnation holds the session's VNI back from reuse for a node that is not in it | `_reclaim_session_keys` sweeps those too, under the same guard, and `_unrecoverable` entries clear once nothing of that incarnation is held anywhere |

NOT done, and still open from this round's review: there is no periodic sweeper -- `reconcile_pool`
runs at manager start and nowhere else -- and `unrecoverable_leaks()` has no caller in production
code. A manager that has been up for a week has neither reconciled nor reported. Wiring both into
the manager's health surface is the remaining piece.

R3 is unchanged and this round does not narrow it. The reconciler is still the most dangerous
thing here: correct by the ownership model, and a release of live tenant state anywhere the model
is wrong. The race above is now covered by a unit test; a rolling restart of two managers against
real nodes is not.


Ninth round, against the same bar:

| # | Was | Now |
|---|-----|-----|
| C22 | the reconciler asked `live == generation`, so a claim carrying NO incarnation was a mismatch against any stamped record -- and that is precisely what the previous version could hand a session whose meta does carry one. The first start of the upgraded manager would have deleted those sessions' live subnet and VNI | judged by `of_generation`, so an unstamped claim under a live record is preserved and the next adoption promotes it |
| C20 | an unstamped child key under a session with NO record was skipped forever, for the same compatibility reason read the other way | where a record exists, a compatible key stays; where there is none, nothing under the id is live and every key goes, stamped or not |
| C20 | pool reconciliation ran only at manager start, so a debt-write-plus-sweep failure went unretried until a restart | the session's own keys are also reconciled whenever its id is used again (three prefix reads on the create/teardown path, not a walk of the pool) |
| — | the sweep read each session's record once per CLAIM | once per session, cached within the sweep; safe only because every delete re-checks the guard, so a stale read can lose a delete but never win one wrongly |

Still NOT done, and carried forward:

- No periodic, leader-only reconciliation. `GlobalTimer` with a distributed lock is the mechanism
  this project already uses (`idle.py`), but wiring it needs a `LockID`, an event type and a
  dispatcher registration, and the plugin holds neither the event producer nor the lock factory.
  An in-plugin timer WITHOUT the lock would be worse than none: every HA manager would scan at
  once. A session id that is never used again therefore still waits for a manager restart.
- `unrecoverable_leaks()` has no production caller and reaches no health surface or metric.
- The startup sweep is unpaginated and unbounded in concurrency.
- `compare_and_delete` is exercised only through the manager's in-memory fake. The transaction it
  builds -- value compares plus `create_revision == 0` for an absent guard -- has no test against
  a real etcd, and that is the primitive the whole reconciler now rests on.

R3 unchanged: no run against this HEAD, and none of C18-C22 or D7-D10 has been exercised on real
nodes.


Tenth round, against the same bar:

| # | Was | Now |
|---|-----|-----|
| C23 | the last round PRESERVED a live unstamped claim and left it unstamped, and nothing on the production path ever promoted it -- `_existing_allocation` returns a READY allocation without touching the pool. Meanwhile `release_all` for ANY earlier incarnation takes an unstamped claim, because unstamped is compatible with all of them. So the window was open for as long as the session lived | the startup sweep stamps what it finds live and unstamped, and the reuse path takes the allocation its record names before handing it back. Both under the record they were judged by |
| C23 | a cleanup knew only its own incarnation, so it could not tell "unstamped and mine" from "unstamped and the live session's" | `release_all` is told what the record names NOW; where that differs from the incarnation being cleaned up, unstamped claims are not its to take. Its own teardown -- where the tombstone IS the live record -- still takes them |
| C20 | the per-session reconcile on id reuse covered child keys only, so an orphan subnet or VNI whose debt note was never written waited for a manager restart | `_reconcile_claims_of` covers the pool half, run where a debt or an unrecorded leak says something is owed under that id rather than on every create |
| C15 | a per-session reconcile that failed was logged and the create carried on | it fails closed with `SessionCleanupPending`; a stale member key holds the VNI back and a stale reservation refuses the next kernel an address, so carrying on builds over state nothing could look at |

The previous round's test for "the allocator still promotes it afterwards" called the allocator
directly, which is not a path a running session takes -- the reuse path does not ask the pool for
a block. Replaced with one that goes through `create_network`.

Still NOT done, unchanged from the last round: no leader-only periodic reconciliation; no
health/metric surface for `unrecoverable_leaks()`; the startup sweep is unpaginated and
unbounded; and `compare_and_delete` is exercised only against the in-memory fake, never a real
etcd transaction -- and the reconciler now rests on it entirely.

R3 unchanged: no run against this HEAD. C18-C23 and D7-D10 remain unexercised on real nodes, and
the upgrade path this round is about -- a session carried across the incarnation field, at the
first start of the manager that upgraded it -- is a rolling restart, which is exactly the test
that has not been run.


Eleventh round, against the same bar:

| # | Was | Now |
|---|-----|-----|
| C24 | `promote` read the pool and handed the block to `_claim_as_ours`, which rewrote each unit by compare-and-swap over whatever bytes it found -- with no check that the bytes were this session's. Called from a record rather than from a claim the pool had just handed out, that is a cross-session overwrite: the block is given back and re-allocated, and s1's promotion rewrites s2's claim into its own | every unit is checked to be this session's claim on this block first, and a partial promotion is undone. The VNI path already did this; the subnet path did not |
| C25 | `_take_allocation` warned on failure and the reuse path carried on, so a record naming an allocation the session does not hold was still handed back as one | it returns whether the allocation is wholly this incarnation's, and the reuse reports no allocation at all when it is not -- the same answer `_still_ours` gives in the same situation. The pool is re-checked once more after the endpoints are written |
| C26 | the sweep asked only `of_generation`, and unstamped is compatible with every incarnation -- so a second, older claim under a live session's id was read as live, never promoted (promotion follows the record) and never reclaimed | an unstamped claim is live only where the record names that very subnet or VNI |
| — | the promotion queue was per CLAIM, so a wide block queued one promotion per unit and each re-read the whole pool: quadratic in legacy sessions | keyed by session |

Still NOT done, unchanged: no leader-only periodic reconciliation; no health surface for
`unrecoverable_leaks()`; the startup sweep is unpaginated; `compare_and_delete` is exercised only
against the in-memory fake.

R3 unchanged. This is the third consecutive round in which the defect found was in code the
previous round added rather than in the original design, and every one of them was in the
reconciliation path. That path is reasoned about only against a model of etcd; it has never run
against a real one, let alone a rolling restart.
