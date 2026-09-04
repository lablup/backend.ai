import asyncio
from pathlib import Path

import pytest

from ai.backend.agent.errors.network import (
    LocalSubnetLayoutChanged,
    LocalSubnetPoolExhausted,
)
from ai.backend.agent.network.local_subnet import (
    DEFAULT_LAYOUT,
    LocalSubnetAllocator,
    LocalSubnetLayout,
    _allocators,
    cluster_host_ips,
    get_local_subnet_allocator,
    host_ipv4_addresses,
)


@pytest.fixture
def state_dir(tmp_path: Path) -> Path:
    return tmp_path / "net-local-subnet"


@pytest.fixture
def tiny_pool() -> LocalSubnetLayout:
    """Two blocks, so exhaustion is reachable in a test."""
    return LocalSubnetLayout.parse("172.30.0.0/29", 30)


def _journal(state_dir: Path, claims: dict[str, str], *, layout: LocalSubnetLayout) -> None:
    """Write a store by hand, as a surviving pre-restart agent would have left it."""
    state_dir.mkdir(parents=True, exist_ok=True)
    (state_dir / ".layout").write_text(layout.serialize())
    for index, session_id in claims.items():
        (state_dir / index).write_text(session_id)


class TestAllocate:
    async def test_idempotent_per_session(self, state_dir: Path) -> None:
        alloc = LocalSubnetAllocator(state_dir)
        assert await alloc.allocate("s1") == await alloc.allocate("s1")

    async def test_distinct_sessions_get_distinct_indices(self, state_dir: Path) -> None:
        alloc = LocalSubnetAllocator(state_dir)
        assert await alloc.allocate("s1") != await alloc.allocate("s2")

    async def test_fills_the_lowest_free_index(self, state_dir: Path) -> None:
        alloc = LocalSubnetAllocator(state_dir)
        for session_id in ("s0", "s1", "s2"):
            await alloc.allocate(session_id)
        await alloc.release("s1")
        assert await alloc.allocate("s3") == 1  # reuses the freed block

    async def test_pool_exhaustion_raises(
        self, state_dir: Path, tiny_pool: LocalSubnetLayout
    ) -> None:
        alloc = LocalSubnetAllocator(state_dir, layout=tiny_pool)
        await alloc.allocate("s1")
        await alloc.allocate("s2")
        with pytest.raises(LocalSubnetPoolExhausted):
            await alloc.allocate("s3")

    async def test_exhaustion_names_the_knob_that_fixes_it(
        self, state_dir: Path, tiny_pool: LocalSubnetLayout
    ) -> None:
        # An operator reading this in a log has to know which setting to change; "pool exhausted"
        # on its own does not tell them the pool is theirs to widen.
        alloc = LocalSubnetAllocator(state_dir, layout=tiny_pool)
        await alloc.allocate("s1")
        await alloc.allocate("s2")

        with pytest.raises(LocalSubnetPoolExhausted) as exc_info:
            await alloc.allocate("s3")

        message = str(exc_info.value)
        assert "container.local-network-block-size" in message
        assert "container.local-network-pool" in message


class TestTheLayout:
    """The pool and the block size are the operator's: the pool must not collide with what the
    host already routes, and the block size trades the node's session ceiling against the
    addresses one session may hold."""

    def test_a_block_is_carved_out_of_the_configured_pool(self) -> None:
        layout = LocalSubnetLayout.parse("10.42.0.0/16", 26)
        assert layout.subnet(0) == "10.42.0.0/26"
        assert layout.subnet(1) == "10.42.0.64/26"
        assert layout.subnet(4) == "10.42.1.0/26"

    def test_the_default_holds_a_thousand_sessions(self) -> None:
        # The /24-per-session default this replaces capped a node at 256 sessions.
        layout = LocalSubnetLayout.parse("172.30.0.0/16", 26)
        assert layout.size == 1024
        assert layout.addresses_per_session == 61

    def test_a_block_bigger_than_its_pool_is_rejected(self) -> None:
        with pytest.raises(ValueError):
            LocalSubnetLayout.parse("172.30.0.0/24", 16)

    async def test_the_allocator_hands_out_subnets_from_it(self, state_dir: Path) -> None:
        alloc = LocalSubnetAllocator(state_dir, layout=LocalSubnetLayout.parse("10.42.0.0/16", 26))
        assert await alloc.allocate_subnet("s1") == "10.42.0.0/26"
        assert await alloc.allocate_subnet("s2") == "10.42.0.64/26"
        assert await alloc.allocate_subnet("s1") == "10.42.0.0/26"  # idempotent


class TestRecuttingThePool:
    """An index names a subnet only against the pool it was cut from. Reading an old index under a
    new pool would name a subnet the live bridge is not on — teardown would delete a device nobody
    owns, and the next session would be handed a block already in use."""

    async def test_a_changed_pool_under_live_sessions_is_refused(self, state_dir: Path) -> None:
        await LocalSubnetAllocator(
            state_dir, layout=LocalSubnetLayout.parse("172.30.0.0/16", 26)
        ).allocate("live")

        restarted = LocalSubnetAllocator(
            state_dir, layout=LocalSubnetLayout.parse("10.42.0.0/16", 26)
        )
        with pytest.raises(LocalSubnetLayoutChanged):
            await restarted.allocate("newcomer")

    async def test_a_changed_block_size_under_live_sessions_is_refused(
        self, state_dir: Path
    ) -> None:
        await LocalSubnetAllocator(
            state_dir, layout=LocalSubnetLayout.parse("172.30.0.0/16", 26)
        ).allocate("live")

        restarted = LocalSubnetAllocator(
            state_dir, layout=LocalSubnetLayout.parse("172.30.0.0/16", 24)
        )
        with pytest.raises(LocalSubnetLayoutChanged):
            await restarted.load()

    async def test_a_drained_node_adopts_the_new_pool(self, state_dir: Path) -> None:
        alloc = LocalSubnetAllocator(state_dir, layout=LocalSubnetLayout.parse("172.30.0.0/16", 26))
        await alloc.allocate("s1")
        await alloc.release("s1")  # drained

        recut = LocalSubnetAllocator(state_dir, layout=LocalSubnetLayout.parse("10.42.0.0/16", 28))
        assert await recut.allocate_subnet("s2") == "10.42.0.0/28"

    async def test_an_unmarked_store_is_held_to_the_pool_it_was_written_from(
        self, state_dir: Path
    ) -> None:
        # A store written before the pool was configurable carries no marker, but it is not
        # ambiguous: that allocator always cut 172.30.0.0/16 into /24s. Under today's /26 default
        # its index 1 would name 172.30.0.64/26, which is not where that session's bridge is.
        state_dir.mkdir(parents=True, exist_ok=True)
        (state_dir / "1").write_text("survivor-of-the-old-agent")

        with pytest.raises(LocalSubnetLayoutChanged):
            await LocalSubnetAllocator(state_dir, layout=DEFAULT_LAYOUT).load()

        legacy = LocalSubnetAllocator(
            state_dir, layout=LocalSubnetLayout.parse("172.30.0.0/16", 24)
        )
        assert await legacy.allocate_subnet("survivor-of-the-old-agent") == "172.30.1.0/24"

    async def test_the_same_pool_replays_normally(self, state_dir: Path) -> None:
        layout = LocalSubnetLayout.parse("10.42.0.0/16", 26)
        held = await LocalSubnetAllocator(state_dir, layout=layout).allocate_subnet("survivor")
        restarted = LocalSubnetAllocator(state_dir, layout=layout)
        assert await restarted.allocate_subnet("survivor") == held


class TestSeveralAgentsOnOneNode:
    """Co-located agents share this journal, because what an index names does not belong to any one
    of them.

    An index becomes the bridge device ``bailo<index>`` and the subnet its gateway sits on — both
    node-global names. Giving each agent its own store (which is what a var-base-path-anchored
    store does) has every agent start counting at 0, so the second one's ``setup_session_network``
    deletes the first one's bridge *by name* while its session is running. Measured on a
    multi-backend node: a containerd cluster session at 0% loss went to 100%, host-side veths gone,
    the moment an apptainer session was created beside it.
    """

    async def test_two_agents_never_get_the_same_block(self, state_dir: Path) -> None:
        containerd = LocalSubnetAllocator(state_dir, owner="i-cd-104")
        apptainer = LocalSubnetAllocator(state_dir, owner="i-sg-104")

        first = await containerd.allocate_subnet("s-cd")
        second = await apptainer.allocate_subnet("s-sg")

        assert first != second

    async def test_an_agent_that_starts_later_sees_the_blocks_already_taken(
        self, state_dir: Path
    ) -> None:
        """The agents do not start together; the second one replays a journal the first wrote."""
        containerd = LocalSubnetAllocator(state_dir, owner="i-cd-104")
        await containerd.allocate("s-cd")

        apptainer = LocalSubnetAllocator(state_dir, owner="i-sg-104")

        assert await apptainer.allocate("s-sg") != 0

    async def test_a_claim_that_appears_after_the_replay_is_taken_not_fatal(
        self, state_dir: Path
    ) -> None:
        """The race the per-agent store was introduced to avoid. Two agents replay an empty
        journal, both pick 0, and one loses the O_EXCL create — which is an ordinary outcome of a
        shared pool, so it takes the next index instead of refusing the session."""
        containerd = LocalSubnetAllocator(state_dir, owner="i-cd-104")
        apptainer = LocalSubnetAllocator(state_dir, owner="i-sg-104")
        await containerd.load()
        await apptainer.load()  # both believe every index is free

        assert await containerd.allocate("s-cd") == 0
        assert await apptainer.allocate("s-sg") == 1

    async def test_an_agent_only_reports_its_own_sessions(self, state_dir: Path) -> None:
        """`sessions()` feeds restart recovery, which reclaims blocks whose session died while the
        agent was down. Returning a neighbour's session there would have this agent free a block
        that is still carrying traffic."""
        containerd = LocalSubnetAllocator(state_dir, owner="i-cd-104")
        apptainer = LocalSubnetAllocator(state_dir, owner="i-sg-104")
        await containerd.allocate("s-cd")
        await apptainer.allocate("s-sg")

        assert await containerd.sessions() == frozenset({"s-cd"})
        assert await apptainer.sessions() == frozenset({"s-sg"})

    async def test_releasing_does_not_touch_a_neighbours_claim(self, state_dir: Path) -> None:
        containerd = LocalSubnetAllocator(state_dir, owner="i-cd-104")
        apptainer = LocalSubnetAllocator(state_dir, owner="i-sg-104")
        await containerd.allocate("s-cd")
        theirs = await apptainer.allocate("s-sg")

        await containerd.release("s-sg")  # not ours; a no-op
        await containerd.release("s-cd")

        assert (state_dir / str(theirs)).exists()
        assert await apptainer.lookup("s-sg") == theirs

    async def test_a_released_block_is_handed_to_whoever_asks_next(self, state_dir: Path) -> None:
        containerd = LocalSubnetAllocator(state_dir, owner="i-cd-104")
        apptainer = LocalSubnetAllocator(state_dir, owner="i-sg-104")
        freed = await containerd.allocate("s-cd")
        await containerd.release("s-cd")

        assert await apptainer.allocate("s-sg") == freed

    async def test_a_claim_written_before_owner_tagging_is_read_as_ours(
        self, state_dir: Path
    ) -> None:
        """A single-agent node upgrading in place over its own journal: those records name no
        owner, and losing track of them would leak the blocks their live sessions still hold."""
        state_dir.mkdir(parents=True, exist_ok=True)
        # The layout marker too: without it the store reads as pre-marker, which is a separate
        # (already covered) refusal and would hide what this case is about.
        (state_dir / ".layout").write_text(DEFAULT_LAYOUT.serialize())
        (state_dir / "0").write_text("s-old")

        alloc = LocalSubnetAllocator(state_dir, owner="i-cd-104")

        assert await alloc.lookup("s-old") == 0
        assert await alloc.allocate("s-new") == 1

    async def test_the_shared_directory_is_writable_by_a_co_located_agent(
        self, state_dir: Path
    ) -> None:
        """Agents may run as different uids (an unprivileged rootless agent beside a root one), so
        the claim directory is created like /tmp — anyone may add, the sticky bit stops anyone
        removing what is not theirs. A root-owned 0755 directory is what made the per-agent store
        look necessary in the first place."""
        await LocalSubnetAllocator(state_dir, owner="i-cd-104").allocate("s-cd")

        mode = state_dir.stat().st_mode & 0o7777
        assert mode == 0o1777, oct(mode)


class TestJournalReplay:
    async def test_load_is_idempotent(self, state_dir: Path) -> None:
        alloc = LocalSubnetAllocator(state_dir)
        await alloc.allocate("s1")
        await alloc.load()
        await alloc.load()
        assert await alloc.lookup("s1") == 0

    async def test_replay_ignores_non_index_entries(self, state_dir: Path) -> None:
        _journal(state_dir, {"0": "s1"}, layout=DEFAULT_LAYOUT)
        (state_dir / "not-an-index").write_text("junk")

        alloc = LocalSubnetAllocator(state_dir)
        assert await alloc.lookup("s1") == 0
        assert await alloc.allocate("s2") == 1

    async def test_replay_keeps_the_lowest_index_of_a_doubly_recorded_session(
        self, state_dir: Path
    ) -> None:
        # A store written by an older, racy allocator can name one session twice.
        _journal(state_dir, {"1": "s1", "3": "s1"}, layout=DEFAULT_LAYOUT)

        alloc = LocalSubnetAllocator(state_dir)
        assert await alloc.lookup("s1") == 1


class TestSingleOwnership:
    """One AgentRuntime hosts a primary plus auxiliary agent in a single event loop. They must
    share the store's one allocator — two instances would each hold their own asyncio.Lock and
    serialize nothing, so the store has a single owner per process instead."""

    def test_one_allocator_per_store(self, state_dir: Path) -> None:
        assert get_local_subnet_allocator(state_dir) is get_local_subnet_allocator(state_dir)

    def test_distinct_stores_get_distinct_allocators(self, state_dir: Path, tmp_path: Path) -> None:
        assert get_local_subnet_allocator(state_dir) is not get_local_subnet_allocator(
            tmp_path / "other"
        )

    async def test_the_shared_owner_serializes_concurrent_agents(self, state_dir: Path) -> None:
        # primary and auxiliary agents resolve the same owner, so their concurrent session setups
        # are serialized by its lock: one session gets one index, distinct sessions get distinct.
        primary = get_local_subnet_allocator(state_dir)
        auxiliary = get_local_subnet_allocator(state_dir)

        same = await asyncio.gather(primary.allocate("shared"), auxiliary.allocate("shared"))
        assert same[0] == same[1]

        distinct = await asyncio.gather(primary.allocate("s1"), auxiliary.allocate("s2"))
        assert len(set(distinct)) == 2


class TestDurability:
    async def test_allocation_survives_a_restart(self, state_dir: Path) -> None:
        held = await LocalSubnetAllocator(state_dir).allocate("survivor")

        restarted = LocalSubnetAllocator(state_dir)  # fresh process, same on-disk store
        assert await restarted.allocate("survivor") == held
        assert await restarted.allocate("newcomer") != held

    async def test_release_survives_a_restart(self, state_dir: Path) -> None:
        held = await LocalSubnetAllocator(state_dir).allocate("s1")
        await LocalSubnetAllocator(state_dir).release("s1")
        assert await LocalSubnetAllocator(state_dir).allocate("s-new") == held


class TestLookup:
    async def test_lookup_does_not_allocate(self, state_dir: Path) -> None:
        alloc = LocalSubnetAllocator(state_dir)
        assert await alloc.lookup("never-seen") is None
        # the absent lookup must not have consumed index 0
        assert await alloc.allocate("s1") == 0

    async def test_lookup_finds_an_allocated_session(self, state_dir: Path) -> None:
        alloc = LocalSubnetAllocator(state_dir)
        index = await alloc.allocate("s1")
        assert await alloc.lookup("s1") == index

    async def test_lookup_after_release_is_none(self, state_dir: Path) -> None:
        alloc = LocalSubnetAllocator(state_dir)
        await alloc.allocate("s1")
        await alloc.release("s1")
        assert await alloc.lookup("s1") is None


class TestClusterHostIps:
    """Single-node cluster peers laid out at deterministic addresses in the session's LOCAL subnet.

    Every kernel computes this independently from the same ordered hostname list (the session-wide
    BACKENDAI_CLUSTER_HOSTS) and the same subnet, so they all agree on the map without coordinating —
    which is what lets each write a correct /etc/hosts before any of them has attached.
    """

    def test_peers_start_after_the_gateway(self) -> None:
        m = cluster_host_ips("172.30.0.0/26", ["main1", "sub1", "sub2"])
        # .1 is the bridge gateway; peers take .2, .3, .4 in order
        assert m == {"main1": "172.30.0.2", "sub1": "172.30.0.3", "sub2": "172.30.0.4"}

    def test_the_layout_is_stable_regardless_of_who_computes_it(self) -> None:
        peers = ["main1", "sub1", "sub2", "sub3"]
        assert cluster_host_ips("10.42.0.0/24", peers) == cluster_host_ips("10.42.0.0/24", peers)

    def test_a_subnet_too_small_for_the_cluster_is_refused(self) -> None:
        # /30 has two usable hosts; one is the gateway, leaving room for exactly one peer.
        with pytest.raises(LocalSubnetPoolExhausted):
            cluster_host_ips("10.0.0.0/30", ["main1", "sub1"])


class TestAdoptingALegacyStore:
    """A node does not upgrade all at once.

    Before this journal was node-wide, every agent kept its own; those stores still name blocks
    whose bridges are up on the host right now. An upgraded agent that started from an empty
    node-wide journal would hand one of them to somebody else. Measured on a half-upgraded node: a
    new agent took the block a legacy enroot session held, and the host ended up with two bridges
    on 172.30.0.64/26 both answering as .65 — the cluster-DNS :53 redirect is keyed on that
    address, so one session's resolver answered for the other and its kernels could not resolve
    their peers (ping and TCP between them still worked, which is what made it look like anything
    but DNS).
    """

    @pytest.fixture
    def legacy(self, tmp_path: Path) -> Path:
        d = tmp_path / "bai-enroot" / "net-local-subnet"
        d.mkdir(parents=True)
        (d / ".layout").write_text(DEFAULT_LAYOUT.serialize())
        return d

    async def test_a_legacy_claim_is_carried_over_at_the_same_index(
        self, state_dir: Path, legacy: Path
    ) -> None:
        """The index names a bridge that already exists, so it is preserved, never re-picked."""
        (legacy / "1").write_text("s-live")

        alloc = LocalSubnetAllocator(state_dir, owner="i-en-104", legacy_dir=legacy)

        assert await alloc.lookup("s-live") == 1
        assert (state_dir / "1").read_text().splitlines()[0] == "s-live"

    async def test_a_co_located_agent_no_longer_gets_that_block(
        self, state_dir: Path, legacy: Path
    ) -> None:
        """The whole point: without adoption the new agent is handed index 1 and the node ends up
        with two bridges on one subnet."""
        (legacy / "1").write_text("s-live")
        await LocalSubnetAllocator(state_dir, owner="i-en-104", legacy_dir=legacy).load()

        newcomer = LocalSubnetAllocator(state_dir, owner="i-sg-104")

        assert await newcomer.allocate("s-new") not in (1,)

    async def test_adoption_is_idempotent_across_restarts(
        self, state_dir: Path, legacy: Path
    ) -> None:
        (legacy / "1").write_text("s-live")
        await LocalSubnetAllocator(state_dir, owner="i-en-104", legacy_dir=legacy).load()

        again = LocalSubnetAllocator(state_dir, owner="i-en-104", legacy_dir=legacy)

        assert await again.lookup("s-live") == 1
        assert sorted(p.name for p in state_dir.iterdir() if p.name.isdigit()) == ["1"]

    async def test_the_legacy_record_survives_adoption(self, state_dir: Path, legacy: Path) -> None:
        """Left in place on purpose: adoption is idempotent, and an operator who rolls this agent
        back to the old code still finds its state."""
        (legacy / "1").write_text("s-live")

        await LocalSubnetAllocator(state_dir, owner="i-en-104", legacy_dir=legacy).load()

        assert (legacy / "1").exists()

    async def test_releasing_prunes_both_records(self, state_dir: Path, legacy: Path) -> None:
        """Otherwise the legacy store only ever grows, and a later restart re-adopts a block whose
        session is long gone."""
        (legacy / "1").write_text("s-live")
        alloc = LocalSubnetAllocator(state_dir, owner="i-en-104", legacy_dir=legacy)
        await alloc.load()

        await alloc.release("s-live")

        assert not (state_dir / "1").exists()
        assert not (legacy / "1").exists()

    async def test_a_block_already_taken_node_wide_is_reported_not_stolen(
        self, state_dir: Path, legacy: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        """A genuine live collision that predates us. The session's bridge is up on that index, so
        it cannot be moved — say so instead of silently allocating around it."""
        await LocalSubnetAllocator(state_dir, owner="i-cd-104").allocate("s-theirs")  # takes 0
        (legacy / "0").write_text("s-ours")

        alloc = LocalSubnetAllocator(state_dir, owner="i-en-104", legacy_dir=legacy)
        with caplog.at_level("ERROR"):
            await alloc.load()

        assert "two bridges now share" in caplog.text
        assert (state_dir / "0").read_text().splitlines()[0] == "s-theirs"

    async def test_an_agent_with_no_legacy_store_is_unaffected(self, state_dir: Path) -> None:
        alloc = LocalSubnetAllocator(state_dir, owner="i-cd-104", legacy_dir=None)

        assert await alloc.allocate("s1") == 0

    async def test_a_legacy_dir_that_is_the_store_itself_is_not_adopted_from(
        self, state_dir: Path
    ) -> None:
        """A single-agent node may already point both at the same path; adopting from itself would
        be a no-op at best and a self-conflict at worst."""
        alloc = LocalSubnetAllocator(state_dir, owner="i-cd-104", legacy_dir=state_dir)

        assert await alloc.allocate("s1") == 0


class TestTheHostIsTheLastWord:
    """A block whose subnet already carries an address on this node is not free, whoever put it
    there.

    Adoption covers this agent's own old store, but not a co-located agent still running the
    pre-node-wide code — its claims live in a store this one cannot even name — nor a bridge left
    behind by a teardown that did not finish, which is journalled nowhere at all. Both leave an
    address on the host. Measured: an upgraded agent was handed the block a legacy session held,
    and the node ended up with two bridges on 172.30.0.64/26 both configured as .65. Peers still
    pinged and still accepted TCP; only DNS broke, because the :53 redirect is keyed on that
    gateway address and one session's resolver answered for the other.
    """

    def _alloc(self, state_dir: Path, addrs: list[str]) -> LocalSubnetAllocator:
        return LocalSubnetAllocator(state_dir, owner="i-sg-104", host_addresses=lambda: addrs)

    async def test_a_block_a_foreign_device_already_holds_is_skipped(self, state_dir: Path) -> None:
        """172.30.0.65 is the gateway of block 1 — exactly what the legacy session's bridge holds."""
        alloc = self._alloc(state_dir, ["192.168.0.104", "172.30.0.65"])

        assert await alloc.allocate("s1") == 0
        assert await alloc.allocate("s2") == 2  # 1 is taken by the device, not by any journal

    async def test_any_address_inside_the_block_counts_not_just_the_gateway(
        self, state_dir: Path
    ) -> None:
        """A container address is as good a proof that the block is live as the gateway is."""
        alloc = self._alloc(state_dir, ["172.30.0.70"])

        assert await alloc.allocate("s1") == 0
        assert await alloc.allocate("s2") == 2

    async def test_addresses_outside_the_pool_are_ignored(self, state_dir: Path) -> None:
        """The node's real NICs, docker0, the k8s CNI — none of them name a block of this pool."""
        alloc = self._alloc(state_dir, ["192.168.0.104", "10.244.1.1", "172.17.0.1"])

        assert await alloc.allocate("s1") == 0
        assert await alloc.allocate("s2") == 1

    def test_the_occupancy_map_holds_only_this_pool(self, state_dir: Path) -> None:
        """Asserted on the map itself, not through `allocate`: an out-of-pool address can only ever
        compute an index outside `range(size)`, so dropping the pool check is invisible from the
        allocation side. It stays because the index arithmetic is what makes that true, and a
        future change to it would otherwise turn every host address into a phantom claim."""
        alloc = self._alloc(state_dir, ["192.168.0.104", "10.244.1.1", "172.17.0.1", "172.30.0.65"])

        assert alloc._blocks_in_use_on_the_host() == {1}

    async def test_a_session_that_already_holds_a_block_still_gets_it_back(
        self, state_dir: Path
    ) -> None:
        """Its own bridge is one of those addresses; re-allocation is a lookup, not a fresh pick,
        so the guard must not lock a session out of the block it is already on."""
        alloc = self._alloc(state_dir, [])
        first = await alloc.allocate("s1")

        alloc._host_addresses = lambda: ["172.30.0.1"]  # its own gateway now up
        assert await alloc.allocate("s1") == first

    async def test_garbage_from_the_host_reader_does_not_stop_allocation(
        self, state_dir: Path
    ) -> None:
        alloc = self._alloc(state_dir, ["not-an-ip", "", "172.30.0.65"])

        assert await alloc.allocate("s1") == 0

    async def test_a_reader_that_returns_nothing_allocates_as_before(self, state_dir: Path) -> None:
        """psutil missing, or the read failing, must degrade to the journal alone rather than
        refusing every session."""
        alloc = self._alloc(state_dir, [])

        assert await alloc.allocate("s1") == 0

    def test_the_production_factory_wires_the_real_reader(self, tmp_path: Path) -> None:
        """The class stays pure so tests are hermetic; the composition root is where the host
        coupling belongs, and forgetting it there is what the guard exists to prevent."""
        alloc = get_local_subnet_allocator(tmp_path / "prod-store")
        try:
            assert alloc._host_addresses is host_ipv4_addresses
        finally:
            _allocators.pop(tmp_path / "prod-store", None)
