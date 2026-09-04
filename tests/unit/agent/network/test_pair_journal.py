"""Node-wide ownership of an ESP pair.

The SA and policy belong to a (self VTEP, peer VTEP, port) triple and are shared by every session
between those two nodes. The refcount deciding when they may go therefore has to be node-wide --
it was per-process, which is only node-wide where one privnet owns the host. With the backend
in-process, two agents on one host each believed they were the pair's only user.
"""

from __future__ import annotations

import asyncio
import os
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

    async def test_a_symlinked_entry_is_refused(self, tmp_path: Path) -> None:
        # The directory is shared by every agent on the node, so a local user can pre-create one
        # of these predictable names pointing at something else; following it would have a process
        # holding CAP_DAC_OVERRIDE truncate whatever it points at.
        root = tmp_path / "net-esp-pair"
        root.mkdir()
        key = pair_key("10.0.0.1", "10.0.0.2", 4789)
        target = tmp_path / "victim"
        target.write_text("do not touch")
        (root / key).symlink_to(target)
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

    async def test_the_lock_file_is_not_the_data_file(self, tmp_path: Path) -> None:
        # The data file is replaced by rename on every write; a lock on it does not survive that.
        journal = _journal(tmp_path)
        key = pair_key("10.0.0.1", "10.0.0.2", 4789)
        await _claim(journal, key, "agent-a", "s1")
        root = tmp_path / "net-esp-pair"
        assert (root / f"{key}.lock").exists()
        assert (root / key).exists()

    async def test_an_emptied_pair_keeps_a_stable_name(self, tmp_path: Path) -> None:
        # Written empty rather than unlinked, so nothing has to reason about the file appearing
        # and disappearing under a lock held elsewhere.
        journal = _journal(tmp_path)
        key = pair_key("10.0.0.1", "10.0.0.2", 4789)
        await _claim(journal, key, "agent-a", "s1")
        await _release(journal, key, "agent-a", "s1")
        assert await journal.users(key) == frozenset()

    async def test_a_leftover_temporary_does_not_block_later_writes(self, tmp_path: Path) -> None:
        # Unique names, not pid-based: a temporary left by a crash used to make every later write
        # fail on O_EXCL once that pid came round again.
        root = tmp_path / "net-esp-pair"
        root.mkdir()
        key = pair_key("10.0.0.1", "10.0.0.2", 4789)
        (root / f".{key}.{os.getpid()}.tmp").write_text("leftover")
        journal = PairJournal(root)
        assert await _claim(journal, key, "agent-a", "s1") is True
