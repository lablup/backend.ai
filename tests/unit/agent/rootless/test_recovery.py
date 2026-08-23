"""Replaying the on-disk container journal after an agent worker restart.

enroot has no daemon and no label store, so a fresh runtime's only record of the containers still
running on the node is this journal. Both directions of getting it wrong are damaging and neither
is loud: dropping a live kernel makes `reconstruct_resource_usage` free its slots and exposes it to
the orphan sweep, while recovering a dead one leaves a phantom kernel holding resources forever.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from ai.backend.agent.rootless.base import RootlessOciRuntime


@pytest.fixture
def journal(runtime: RootlessOciRuntime) -> Path:
    runtime._state_path.mkdir(parents=True, exist_ok=True)
    return runtime._state_path


def _entry(journal: Path, container_id: str, **meta: object) -> Path:
    path = journal / container_id
    path.mkdir(parents=True, exist_ok=True)
    (path / "container.json").write_text(json.dumps(meta))
    return path


def _pretend(
    runtime: RootlessOciRuntime,
    monkeypatch: pytest.MonkeyPatch,
    *,
    alive: dict[int, bool],
    start_times: dict[int, int],
) -> None:
    """Stand in for /proc, which a unit test cannot arrange live processes in."""
    monkeypatch.setattr(runtime, "_alive", lambda pid: alive.get(pid, False))
    monkeypatch.setattr(runtime, "_pid_start_time", lambda pid: start_times.get(pid))


class TestRecovery:
    def test_a_live_container_comes_back(
        self, runtime: RootlessOciRuntime, journal: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _entry(
            journal,
            "kernel-1",
            pid=4242,
            start_time=99,
            image="registry/py:3.12",
            labels={"ai.backend.kernel-id": "k1"},
        )
        _pretend(runtime, monkeypatch, alive={4242: True}, start_times={4242: 99})

        runtime._recover_containers()

        assert runtime._pids == {"kernel-1": 4242}
        assert runtime._images["kernel-1"] == "registry/py:3.12"
        assert runtime._labels["kernel-1"] == {"ai.backend.kernel-id": "k1"}

    def test_labels_survive_because_reconciliation_needs_them(
        self, runtime: RootlessOciRuntime, journal: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """`enumerate_containers` filters on these to rebuild the resource allocation map — an
        empty set here drops every enroot container from `reconstruct_resource_usage` even though
        the PID was recovered correctly."""
        _entry(journal, "kernel-1", pid=1, start_time=1, labels={"a": "1", "b": "2"})
        _pretend(runtime, monkeypatch, alive={1: True}, start_times={1: 1})

        runtime._recover_containers()

        assert runtime._labels["kernel-1"] == {"a": "1", "b": "2"}


class TestStaleEntries:
    def test_a_dead_pid_is_dropped(
        self, runtime: RootlessOciRuntime, journal: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        entry = _entry(journal, "kernel-gone", pid=4242, start_time=99)
        _pretend(runtime, monkeypatch, alive={}, start_times={})

        runtime._recover_containers()

        assert runtime._pids == {}
        assert not entry.exists()

    def test_a_zombie_is_not_alive(
        self, runtime: RootlessOciRuntime, journal: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """`os.kill(pid, 0)` succeeds for a zombie, and the pod's supervisor does not reap a dead
        worker's orphans, so zombies genuinely linger here. `_alive` reads the state character for
        exactly this case; recovering one produces a kernel that is reported running forever."""
        _entry(journal, "kernel-zombie", pid=4242, start_time=99)
        monkeypatch.setattr(runtime, "_proc_stat_fields", lambda pid: ["Z", "1", *["0"] * 30])

        runtime._recover_containers()

        assert runtime._pids == {}

    def test_a_recycled_pid_is_rejected(
        self, runtime: RootlessOciRuntime, journal: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """The whole reason the start time is journalled: the kernel reuses PIDs, and matching on
        the number alone would hand a recovered kernel some unrelated process to signal and kill."""
        _entry(journal, "kernel-1", pid=4242, start_time=99)
        _pretend(runtime, monkeypatch, alive={4242: True}, start_times={4242: 100})

        runtime._recover_containers()

        assert runtime._pids == {}


class TestMalformedJournal:
    def test_one_bad_entry_does_not_lose_the_others(
        self, runtime: RootlessOciRuntime, journal: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Recovery runs in `open()`. Raising here would fail agent startup outright, and the
        cheapest way to hit it is a journal truncated by a node that lost power."""
        (journal / "kernel-corrupt").mkdir()
        (journal / "kernel-corrupt" / "container.json").write_text("{not json")
        _entry(journal, "kernel-ok", pid=1, start_time=1)
        _pretend(runtime, monkeypatch, alive={1: True}, start_times={1: 1})

        runtime._recover_containers()

        assert runtime._pids == {"kernel-ok": 1}

    def test_a_state_dir_without_a_journal_is_ignored(
        self, runtime: RootlessOciRuntime, journal: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """The gate dir is created before the journal is written, so a container killed in that
        window leaves a state dir with no `container.json`."""
        (journal / "kernel-half-made").mkdir()
        _pretend(runtime, monkeypatch, alive={}, start_times={})

        runtime._recover_containers()

        assert runtime._pids == {}

    def test_an_entry_without_a_pid_is_ignored(
        self, runtime: RootlessOciRuntime, journal: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _entry(journal, "kernel-1", start_time=1, image="x")
        _pretend(runtime, monkeypatch, alive={}, start_times={})

        runtime._recover_containers()

        assert runtime._pids == {}

    def test_no_state_path_at_all(self, runtime: RootlessOciRuntime) -> None:
        """First ever start: `open()` calls this before anything has been created."""
        runtime._recover_containers()

        assert runtime._pids == {}


class TestRoundTrip:
    def test_what_is_recorded_is_what_comes_back(
        self, runtime: RootlessOciRuntime, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """The writer and the reader are the only two users of this format, so pin them together
        rather than to a literal document."""
        runtime._state_path.mkdir(parents=True, exist_ok=True)
        runtime._images["kernel-1"] = "registry/py:3.12"
        runtime._labels["kernel-1"] = {"ai.backend.kernel-id": "k1"}
        monkeypatch.setattr(runtime, "_pid_start_time", lambda pid: 99)

        runtime._record_container("kernel-1", 4242)
        runtime._pids.clear()
        runtime._images.clear()
        runtime._labels.clear()
        monkeypatch.setattr(runtime, "_alive", lambda pid: True)
        runtime._recover_containers()

        assert runtime._pids == {"kernel-1": 4242}
        assert runtime._images == {"kernel-1": "registry/py:3.12"}
        assert runtime._labels == {"kernel-1": {"ai.backend.kernel-id": "k1"}}
