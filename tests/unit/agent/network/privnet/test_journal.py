"""The privnet's durable record — what it holds, and who can read it.

The privnet holds no etcd client by design (it is the process that owns CAP_NET_ADMIN, and the
fewer things it talks to the smaller the blast radius), so this journal is its ONLY way to rebuild
a session after its own restart. That makes the session record the one place on the node where the
overlay's IPsec key sits at rest.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from ai.backend.agent.network.privnet.journal import PrivNetJournal


def _config(**over: object) -> dict[str, object]:
    return {
        "backend": "vxlan",
        "subnet": "10.128.7.0/24",
        "vni": 4103,
        "mtu": 1450,
        "encryption_key": "de" * 32,
        **over,
    }


def _mode(path: Path) -> int:
    return path.stat().st_mode & 0o777


@pytest.fixture
def journal(tmp_path: Path) -> PrivNetJournal:
    return PrivNetJournal(tmp_path / "net-privnet")


class TestTheRecordIsOwnerOnly:
    """Measured before this was enforced: the session record landed at 0664 inside a 0775
    directory, i.e. any local user could read the overlay's encryption key. The socket next to it
    was already chmod 0600; the journal was left to the umask."""

    @pytest.mark.skipif(os.geteuid() == 0, reason="root reads everything regardless")
    async def test_a_session_record_is_not_readable_by_anyone_else(
        self, journal: PrivNetJournal, tmp_path: Path
    ) -> None:
        await journal.record_session("sess-a", _config())

        record = tmp_path / "net-privnet" / "sessions" / "sess-a"
        assert _mode(record) == 0o600, oct(_mode(record))

    async def test_the_directories_are_owner_only_too(
        self, journal: PrivNetJournal, tmp_path: Path
    ) -> None:
        """A 0600 file under a traversable directory is still a filename anyone can stat, and the
        temp file the write goes through lives there for a moment."""
        await journal.record_session("sess-a", _config())

        root = tmp_path / "net-privnet"
        assert _mode(root) == 0o700, oct(_mode(root))
        assert _mode(root / "sessions") == 0o700, oct(_mode(root / "sessions"))

    async def test_an_attachment_record_is_locked_down_as_well(
        self, journal: PrivNetJournal, tmp_path: Path
    ) -> None:
        await journal.record_attachment("c1", "sess-a", "10.128.7.1")

        assert _mode(tmp_path / "net-privnet" / "attachments" / "c1") == 0o600
        assert _mode(tmp_path / "net-privnet" / "attachments") == 0o700

    async def test_a_tree_an_earlier_release_left_open_is_tightened(
        self, journal: PrivNetJournal, tmp_path: Path
    ) -> None:
        """`mkdir(mode=...)` is ignored for a directory that already exists, so an upgrade over a
        node that ran the permissive version would otherwise keep its 0755 directories forever."""
        root = tmp_path / "net-privnet"
        (root / "sessions").mkdir(parents=True)
        root.chmod(0o755)
        (root / "sessions").chmod(0o755)

        await journal.record_session("sess-a", _config())

        assert _mode(root) == 0o700
        assert _mode(root / "sessions") == 0o700


class TestWhatIsKept:
    async def test_the_config_round_trips(self, journal: PrivNetJournal) -> None:
        """The key stays in the record: this journal is the privnet's only durable state, so a
        restart that lost it could not rebuild an encrypted session's data plane."""
        await journal.record_session("sess-a", _config())

        assert await journal.sessions() == {"sess-a": _config()}

    async def test_a_record_is_replaced_not_appended(self, journal: PrivNetJournal) -> None:
        await journal.record_session("sess-a", _config(vni=1))
        await journal.record_session("sess-a", _config(vni=2))

        assert (await journal.sessions())["sess-a"]["vni"] == 2

    async def test_forgetting_a_session_removes_it(self, journal: PrivNetJournal) -> None:
        await journal.record_session("sess-a", _config())
        await journal.forget_session("sess-a")

        assert await journal.sessions() == {}

    async def test_forgetting_one_that_was_never_there_is_not_an_error(
        self, journal: PrivNetJournal
    ) -> None:
        """Teardown runs unconditionally, including for a session set up before a restart that
        never got journalled."""
        await journal.forget_session("sess-never")


class TestAPartialWriteIsNeverRead:
    async def test_a_half_written_record_does_not_become_a_session(
        self, journal: PrivNetJournal, tmp_path: Path
    ) -> None:
        """The write goes through a temp file for exactly this: a truncated record read on the next
        boot would name a session whose subnet cannot be parsed, and the reconcile pass would skip
        it forever."""
        await journal.record_session("sess-a", _config())
        sessions = tmp_path / "net-privnet" / "sessions"
        (sessions / ".sess-b.tmp").write_text('{"backend": "vx')

        assert set(await journal.sessions()) == {"sess-a"}

    async def test_an_unreadable_record_is_dropped_rather_than_raising(
        self, journal: PrivNetJournal, tmp_path: Path
    ) -> None:
        """Recovery runs at daemon boot; raising here would leave a node whose devices are up and
        whose owner refuses every verb about them."""
        await journal.record_session("sess-a", _config())
        (tmp_path / "net-privnet" / "sessions" / "sess-bad").write_text("{not json")

        assert set(await journal.sessions()) == {"sess-a"}

    async def test_no_journal_at_all_reads_empty(self, journal: PrivNetJournal) -> None:
        assert await journal.sessions() == {}
        assert await journal.attachments() == {}


class TestAttachments:
    async def test_what_was_attached_comes_back(self, journal: PrivNetJournal) -> None:
        await journal.record_attachment("c1", "sess-a", "10.128.7.1")

        records = await journal.attachments()
        assert records["c1"].session_id == "sess-a"
        assert records["c1"].overlay_ip == "10.128.7.1"

    async def test_a_bridge_attachment_has_no_overlay_ip(self, journal: PrivNetJournal) -> None:
        """Single-node sessions carry no overlay address; None must survive the round trip rather
        than becoming the string 'None'."""
        await journal.record_attachment("c1", "sess-a", None)

        assert (await journal.attachments())["c1"].overlay_ip is None

    async def test_the_record_is_json_a_human_can_read(
        self, journal: PrivNetJournal, tmp_path: Path
    ) -> None:
        """It is the file an operator reaches for when a node's devices outlive their daemon."""
        await journal.record_attachment("c1", "sess-a", "10.128.7.1")

        raw = json.loads((tmp_path / "net-privnet" / "attachments" / "c1").read_text())
        assert raw["session_id"] == "sess-a"
