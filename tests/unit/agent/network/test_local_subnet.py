import asyncio
from pathlib import Path

import pytest

from ai.backend.agent.errors.network import LocalSubnetPoolExhausted, NetworkStateStoreConflict
from ai.backend.agent.network.local_subnet import (
    LocalSubnetAllocator,
    get_local_subnet_allocator,
)


@pytest.fixture
def state_dir(tmp_path: Path) -> Path:
    return tmp_path / "net-local-subnet"


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

    async def test_pool_exhaustion_raises(self, state_dir: Path) -> None:
        alloc = LocalSubnetAllocator(state_dir, pool_size=2)
        await alloc.allocate("s1")
        await alloc.allocate("s2")
        with pytest.raises(LocalSubnetPoolExhausted):
            await alloc.allocate("s3")


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
        state_dir.mkdir(parents=True, exist_ok=True)
        (state_dir / "0").write_text("s1")
        (state_dir / "not-an-index").write_text("junk")

        alloc = LocalSubnetAllocator(state_dir)
        assert await alloc.lookup("s1") == 0
        assert await alloc.allocate("s2") == 1

    async def test_replay_keeps_the_lowest_index_of_a_doubly_recorded_session(
        self, state_dir: Path
    ) -> None:
        # A store written by an older, racy allocator can name one session twice.
        state_dir.mkdir(parents=True, exist_ok=True)
        (state_dir / "1").write_text("s1")
        (state_dir / "3").write_text("s1")

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
