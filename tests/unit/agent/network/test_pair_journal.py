"""Node-wide ownership of an ESP pair.

The SA and policy belong to a (self VTEP, peer VTEP, port) triple and are shared by every session
between those two nodes. The refcount deciding when they may go therefore has to be node-wide --
it was per-process, which is only node-wide where one privnet owns the host. With the backend
in-process, two agents on one host each believed they were the pair's only user.
"""

from __future__ import annotations

from pathlib import Path

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


class TestNodeWideRefcount:
    def test_the_last_user_on_the_node_frees_the_pair(self, tmp_path: Path) -> None:
        journal = _journal(tmp_path)
        key = pair_key("10.0.0.1", "10.0.0.2", 4789)
        journal.claim(key, "agent-a", "s1")
        assert journal.release(key, "agent-a", "s1") is True

    def test_another_agents_claim_keeps_the_pair(self, tmp_path: Path) -> None:
        # This is the case the in-process refcount could not see: agent-b's session is carried by
        # the very SA and policy agent-a is about to remove.
        journal = _journal(tmp_path)
        key = pair_key("10.0.0.1", "10.0.0.2", 4789)
        journal.claim(key, "agent-a", "s1")
        journal.claim(key, "agent-b", "s2")
        assert journal.release(key, "agent-a", "s1") is False
        assert journal.users(key) == frozenset({"agent-b/s2"})

    def test_releasing_twice_is_harmless(self, tmp_path: Path) -> None:
        journal = _journal(tmp_path)
        key = pair_key("10.0.0.1", "10.0.0.2", 4789)
        journal.claim(key, "agent-a", "s1")
        assert journal.release(key, "agent-a", "s1") is True
        assert journal.release(key, "agent-a", "s1") is True

    def test_an_unwritable_root_reports_unknown_rather_than_free(self, tmp_path: Path) -> None:
        # None, not True: answering "free" from a journal that could not be read is how the pair
        # gets removed out from under whoever else is on it.
        blocked = tmp_path / "file"
        blocked.write_text("not a directory")
        journal = PairJournal(blocked / "net-esp-pair")
        assert journal.release(pair_key("10.0.0.1", "10.0.0.2", 4789), "agent-a", "s1") is None


class TestPruningAPreviousLife:
    """Claims outlive the process that made them. A crash between programming a pair and tearing
    it down leaves one with nobody behind it, and the pair it names is then never removed."""

    def test_this_owners_dead_claims_go(self, tmp_path: Path) -> None:
        journal = _journal(tmp_path)
        key = pair_key("10.0.0.1", "10.0.0.2", 4789)
        journal.claim(key, "agent-a", "s1")
        assert journal.prune("agent-a", live_sessions=()) == 1
        assert journal.users(key) == frozenset()

    def test_this_owners_live_claims_stay(self, tmp_path: Path) -> None:
        journal = _journal(tmp_path)
        key = pair_key("10.0.0.1", "10.0.0.2", 4789)
        journal.claim(key, "agent-a", "s1")
        assert journal.prune("agent-a", live_sessions=("s1",)) == 0
        assert journal.users(key) == frozenset({"agent-a/s1"})

    def test_another_agents_claims_are_never_touched(self, tmp_path: Path) -> None:
        # Treating a co-located agent's claims as dead is precisely the bug this journal exists
        # to prevent.
        journal = _journal(tmp_path)
        key = pair_key("10.0.0.1", "10.0.0.2", 4789)
        journal.claim(key, "agent-b", "s2")
        assert journal.prune("agent-a", live_sessions=()) == 0
        assert journal.users(key) == frozenset({"agent-b/s2"})

    def test_a_restarted_agent_keeps_the_same_name(self, tmp_path: Path) -> None:
        # The owner is the agent id, not a pid: a pid would make every claim from the previous
        # life unrecognisable, so none of them would ever be pruned or released.
        journal = _journal(tmp_path)
        key = pair_key("10.0.0.1", "10.0.0.2", 4789)
        journal.claim(key, "i-dk-104", "s1")
        assert journal.prune("i-dk-104", live_sessions=()) == 1
