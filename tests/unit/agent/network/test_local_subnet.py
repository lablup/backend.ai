import asyncio
from pathlib import Path

import pytest

from ai.backend.agent.errors.network import (
    LocalSubnetLayoutChanged,
    LocalSubnetPoolExhausted,
    NetworkStateStoreConflict,
)
from ai.backend.agent.network.local_subnet import (
    DEFAULT_LAYOUT,
    LocalSubnetAllocator,
    LocalSubnetLayout,
    cluster_host_ips,
    get_local_subnet_allocator,
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


class TestForeignWriter:
    """The store has one writer per node. A record that exists on disk while the owner believes
    the index free means a second writer is mutating this node's network, which the data plane
    cannot survive anyway. It must be reported, never allocated around."""

    async def test_a_record_appearing_behind_the_owner_raises(self, state_dir: Path) -> None:
        alloc = LocalSubnetAllocator(state_dir)
        await alloc.load()  # owner's memory is now authoritative and empty

        state_dir.mkdir(parents=True, exist_ok=True)
        (state_dir / "0").write_text("written-by-someone-else")

        with pytest.raises(NetworkStateStoreConflict):
            await alloc.allocate("s1")

    async def test_the_foreign_record_is_left_intact(self, state_dir: Path) -> None:
        alloc = LocalSubnetAllocator(state_dir)
        await alloc.load()
        state_dir.mkdir(parents=True, exist_ok=True)
        (state_dir / "0").write_text("written-by-someone-else")

        with pytest.raises(NetworkStateStoreConflict):
            await alloc.allocate("s1")
        assert (state_dir / "0").read_text() == "written-by-someone-else"


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
