"""Node-wide ownership of an ESP pair.

The SA and policy belong to a (self VTEP, peer VTEP, port) triple and are shared by every session
between those two nodes. The refcount deciding when they may go therefore has to be node-wide --
it was per-process, which is only node-wide where one privnet owns the host. With the backend
in-process, two agents on one host each believed they were the pair's only user.
"""

from __future__ import annotations

import asyncio
import os
import stat
from pathlib import Path

import pytest

from ai.backend.agent.network.pair_journal import PairJournal, pair_key


def _journal(tmp_path: Path) -> PairJournal:
    return PairJournal(tmp_path / "net-esp-pair")


class TestPairKey:
    def test_it_is_directed(self) -> None:
        # The SAs are, so the claims must be too.
        assert pair_key("10.0.0.1", "10.0.0.2", 4789) != pair_key("10.0.0.2", "10.0.0.1", 4789)

    def test_the_port_is_part_of_it(self) -> None:
        assert pair_key("10.0.0.1", "10.0.0.2", 4789) != pair_key("10.0.0.1", "10.0.0.2", 4790)

    def test_it_is_a_usable_filename(self) -> None:
        assert "/" not in pair_key("10.0.0.1", "10.0.0.2", 4789)


async def _claim(journal: PairJournal, key: str, owner: str, session: str) -> bool:
    async with journal.claiming(key, owner, session) as recorded:
        return recorded


async def _release(journal: PairJournal, key: str, owner: str, session: str) -> bool | None:
    async with journal.releasing(key, owner, session) as free:
        return free


class TestNodeWideRefcount:
    async def test_the_last_user_on_the_node_frees_the_pair(self, tmp_path: Path) -> None:
        journal = _journal(tmp_path)
        key = pair_key("10.0.0.1", "10.0.0.2", 4789)
        assert await _claim(journal, key, "agent-a", "s1") is True
        assert await _release(journal, key, "agent-a", "s1") is True

    async def test_another_agents_claim_keeps_the_pair(self, tmp_path: Path) -> None:
        # This is the case the in-process refcount could not see: agent-b's session is carried by
        # the very SA and policy agent-a is about to remove.
        journal = _journal(tmp_path)
        key = pair_key("10.0.0.1", "10.0.0.2", 4789)
        await _claim(journal, key, "agent-a", "s1")
        await _claim(journal, key, "agent-b", "s2")
        assert await _release(journal, key, "agent-a", "s1") is False
        assert await journal.users(key) == frozenset({"agent-b/s2"})

    async def test_releasing_twice_is_harmless(self, tmp_path: Path) -> None:
        journal = _journal(tmp_path)
        key = pair_key("10.0.0.1", "10.0.0.2", 4789)
        await _claim(journal, key, "agent-a", "s1")
        assert await _release(journal, key, "agent-a", "s1") is True
        assert await _release(journal, key, "agent-a", "s1") is True

    async def test_an_unreachable_journal_reports_unknown_rather_than_free(
        self, tmp_path: Path
    ) -> None:
        # None, not True: answering "free" from a journal that could not be read is how the pair
        # gets removed out from under whoever else is on it.
        blocked = tmp_path / "file"
        blocked.write_text("not a directory")
        journal = PairJournal(blocked / "net-esp-pair")
        assert await _release(journal, pair_key("10.0.0.1", "10.0.0.2", 4789), "a", "s1") is None

    async def test_an_unreachable_journal_reports_the_claim_as_unrecorded(
        self, tmp_path: Path
    ) -> None:
        # The caller has to know: with no claim on disk, no later release may conclude from this
        # journal that the pair is free.
        blocked = tmp_path / "file"
        blocked.write_text("not a directory")
        journal = PairJournal(blocked / "net-esp-pair")
        assert await _claim(journal, pair_key("10.0.0.1", "10.0.0.2", 4789), "a", "s1") is False

    async def test_a_symlinked_lock_is_refused(self, tmp_path: Path) -> None:
        # The directory is shared by every agent on the node, so a local user can pre-create one
        # of these predictable names pointing at something else; following it would have a process
        # holding CAP_DAC_OVERRIDE open whatever it points at.
        root = tmp_path / "net-esp-pair"
        key = pair_key("10.0.0.1", "10.0.0.2", 4789)
        (root / key).mkdir(parents=True)
        target = tmp_path / "victim"
        target.write_text("do not touch")
        (root / key / ".lock").symlink_to(target)
        journal = PairJournal(root)
        assert await _claim(journal, key, "agent-a", "s1") is False
        assert target.read_text() == "do not touch"


class TestPruningAPreviousLife:
    """Claims outlive the process that made them. A crash between programming a pair and tearing
    it down leaves one with nobody behind it, and the pair it names is then never removed."""

    async def test_this_owners_dead_claims_go(self, tmp_path: Path) -> None:
        journal = _journal(tmp_path)
        key = pair_key("10.0.0.1", "10.0.0.2", 4789)
        await _claim(journal, key, "agent-a", "s1")
        assert await journal.prune("agent-a", live_sessions=()) == 1
        assert await journal.users(key) == frozenset()

    async def test_this_owners_live_claims_stay(self, tmp_path: Path) -> None:
        journal = _journal(tmp_path)
        key = pair_key("10.0.0.1", "10.0.0.2", 4789)
        await _claim(journal, key, "agent-a", "s1")
        assert await journal.prune("agent-a", live_sessions=("s1",)) == 0
        assert await journal.users(key) == frozenset({"agent-a/s1"})

    async def test_another_agents_claims_are_never_touched(self, tmp_path: Path) -> None:
        # Treating a co-located agent's claims as dead is precisely the bug this journal exists
        # to prevent.
        journal = _journal(tmp_path)
        key = pair_key("10.0.0.1", "10.0.0.2", 4789)
        await _claim(journal, key, "agent-b", "s2")
        assert await journal.prune("agent-a", live_sessions=()) == 0
        assert await journal.users(key) == frozenset({"agent-b/s2"})

    async def test_a_restarted_agent_keeps_the_same_name(self, tmp_path: Path) -> None:
        # The owner is the agent id, not a pid: a pid would make every claim from the previous
        # life unrecognisable, so none of them would ever be pruned or released.
        journal = _journal(tmp_path)
        key = pair_key("10.0.0.1", "10.0.0.2", 4789)
        await _claim(journal, key, "i-dk-104", "s1")
        assert await journal.prune("i-dk-104", live_sessions=()) == 1


class TestTheLockActuallyExcludes:
    """The lock used to be taken on the data file, which `_write` replaces by rename -- so the
    moment a writer published, the lock it still held was on an inode nobody would open again and
    the next process locked the new one straight away. Reproduced with two journal instances."""

    async def test_a_second_holder_waits_for_the_first(self, tmp_path: Path) -> None:
        a, b = _journal(tmp_path), _journal(tmp_path)
        key = pair_key("10.0.0.1", "10.0.0.2", 4789)
        await _claim(a, key, "agent-a", "s1")
        entered = asyncio.Event()

        async def second() -> None:
            async with b.claiming(key, "agent-b", "s2"):
                entered.set()

        async with a.releasing(key, "agent-a", "s1"):
            task = asyncio.create_task(second())
            with pytest.raises(TimeoutError):
                await asyncio.wait_for(asyncio.shield(entered.wait()), timeout=1.0)
        await task
        assert entered.is_set()

    async def test_the_lock_is_a_name_of_its_own(self, tmp_path: Path) -> None:
        # Never a file that gets removed: a lock on a claim file dies with the claim.
        journal = _journal(tmp_path)
        key = pair_key("10.0.0.1", "10.0.0.2", 4789)
        await _claim(journal, key, "agent-a", "s1")
        pair_dir = tmp_path / "net-esp-pair" / key
        assert (pair_dir / ".lock").is_file()
        await _release(journal, key, "agent-a", "s1")
        assert (pair_dir / ".lock").is_file()

    async def test_each_claim_is_its_own_file(self, tmp_path: Path) -> None:
        # Nothing rewrites another agent's file, which is what lets agents running as different
        # users share the journal: the sticky bit protects each one's claims instead of blocking
        # a shared file's replacement.
        journal = _journal(tmp_path)
        key = pair_key("10.0.0.1", "10.0.0.2", 4789)
        await _claim(journal, key, "agent-a", "s1")
        await _claim(journal, key, "agent-b", "s2")
        pair_dir = tmp_path / "net-esp-pair" / key
        names = {p.name for p in pair_dir.iterdir() if p.name != ".lock"}
        assert names == {"agent-a~s1", "agent-b~s2"}

    async def test_an_emptied_pair_keeps_a_stable_name(self, tmp_path: Path) -> None:
        # Written empty rather than unlinked, so nothing has to reason about the file appearing
        # and disappearing under a lock held elsewhere.
        journal = _journal(tmp_path)
        key = pair_key("10.0.0.1", "10.0.0.2", 4789)
        await _claim(journal, key, "agent-a", "s1")
        await _release(journal, key, "agent-a", "s1")
        assert await journal.users(key) == frozenset()

    async def test_a_claim_survives_being_recorded_twice(self, tmp_path: Path) -> None:
        # Re-programming a pair re-records the claim; it must not fail the second time.
        journal = _journal(tmp_path)
        key = pair_key("10.0.0.1", "10.0.0.2", 4789)
        assert await _claim(journal, key, "agent-a", "s1") is True
        assert await _claim(journal, key, "agent-a", "s1") is True
        assert await journal.users(key) == frozenset({"agent-a/s1"})


class TestHostileNeighbours:
    """The journal lives in a world-writable directory with predictable names, so a local user can
    pre-create any of them. Each of these was reproduced against an earlier version."""

    async def test_a_directory_symlink_is_not_followed(self, tmp_path: Path) -> None:
        # Reproduced: a 0o700 directory came back 0o1777 with the journal's files inside it,
        # because `mkdir(exist_ok=True)` succeeds through a symlink and `chmod` follows it.
        root = tmp_path / "net-esp-pair"
        root.mkdir()
        victim = tmp_path / "victim"
        victim.mkdir(mode=0o700)
        key = pair_key("10.0.0.1", "10.0.0.2", 4789)
        (root / key).symlink_to(victim)

        assert await _claim(PairJournal(root), key, "agent-a", "s1") is False
        assert stat.S_IMODE(victim.stat().st_mode) == 0o700
        assert list(victim.iterdir()) == []

    async def test_a_fifo_lock_does_not_block(self, tmp_path: Path) -> None:
        # Reproduced: opening a FIFO read-only waits for a writer that never comes, and it is the
        # THREAD that blocks -- the whole interpreter hung, so not even a timeout could fire.
        # O_NOFOLLOW does not cover this; O_NONBLOCK plus the regular-file check does.
        root = tmp_path / "net-esp-pair"
        key = pair_key("10.0.0.1", "10.0.0.2", 4789)
        (root / key).mkdir(parents=True)
        os.mkfifo(root / key / ".lock")

        async with asyncio.timeout(5):
            assert await _claim(PairJournal(root), key, "agent-a", "s1") is False

    async def test_the_root_is_world_writable(self, tmp_path: Path) -> None:
        # Created by `mkdir(parents=True)` it carries the process umask, and a root at 0o775 is
        # one a co-located agent running as another user cannot create a new pair in.
        root = tmp_path / "net-esp-pair"
        await _claim(_journal(tmp_path), pair_key("10.0.0.1", "10.0.0.2", 4789), "a", "s1")
        assert stat.S_IMODE(root.stat().st_mode) == 0o1777

    async def test_the_lock_is_readable_by_other_agents(self, tmp_path: Path) -> None:
        # `open`'s mode is masked by umask; a lock left at 0o600 is one no other agent can open.
        root = tmp_path / "net-esp-pair"
        key = pair_key("10.0.0.1", "10.0.0.2", 4789)
        await _claim(_journal(tmp_path), key, "agent-a", "s1")
        assert stat.S_IMODE((root / key / ".lock").stat().st_mode) & 0o044 == 0o044
