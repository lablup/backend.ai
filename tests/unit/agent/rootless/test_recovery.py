"""Replaying the on-disk container journal after an agent worker restart.

enroot has no daemon and no label store, so a fresh runtime's only record of the containers still
running on the node is this journal. Both directions of getting it wrong are damaging and neither
is loud: dropping a live kernel makes `reconstruct_resource_usage` free its slots and exposes it to
the orphan sweep, while recovering a dead one leaves a phantom kernel holding resources forever.
"""

from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path
from typing import Any

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


def _second_instance(runtime: RootlessOciRuntime) -> RootlessOciRuntime:
    """Another client over the same roots — what privnet is relative to the agent."""
    return type(runtime)(
        data_path=runtime._data_path,
        cache_path=runtime._cache_path,
        runtime_path=runtime._runtime_path,
        state_path=runtime._state_path,
        kernel_uid=1000,
        kernel_gid=1000,
    )


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


class TestASecondProcessCanReadTheJournal:
    """privnet holds its own runtime client and is asked about containers it never created — the
    agent made them. The journal, not this instance's memory, is the shared record, so a miss has
    to fall back to it rather than answer "no such container"."""

    async def test_container_pid_falls_back_to_the_journal_on_a_miss(
        self, runtime: RootlessOciRuntime, journal: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        reader = _second_instance(runtime)
        _entry(journal, "c1", pid=4321, start_time=42, image="img:1", labels={})
        _pretend(reader, monkeypatch, alive={4321: True}, start_times={4321: 42})

        assert reader._pids == {}, "the reader has never seen this container"
        assert await reader.container_pid("c1") == 4321

    async def test_a_stale_journal_entry_is_still_refused(
        self, runtime: RootlessOciRuntime, journal: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """The liveness + start-time check is what makes the fallback safe: a recycled PID must not
        be handed out as a live container."""
        reader = _second_instance(runtime)
        _entry(journal, "c1", pid=4321, start_time=42, image="img:1", labels={})
        _pretend(reader, monkeypatch, alive={4321: True}, start_times={4321: 99})  # recycled

        assert await reader.container_pid("c1") is None

    async def test_list_container_infos_sees_what_arrived_after_open(
        self, runtime: RootlessOciRuntime, journal: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _pretend(runtime, monkeypatch, alive={7: True}, start_times={7: 1})
        assert list(await runtime.list_container_infos()) == []

        _entry(journal, "c2", pid=7, start_time=1, image="img:2", labels={"a": "b"})

        infos = list(await runtime.list_container_infos())
        assert [i.id for i in infos] == ["c2"]
        assert infos[0].labels == {"a": "b"}


class TestTheKernelOutlivesTheAgent:
    """Everything above only means something if the kernel is still there to recover.

    These runtimes have no daemon: the kernel is a direct CHILD of the agent process. Inheriting
    the agent's process group makes it reachable by any signal aimed at that group — an operator's
    Ctrl+C, a closing terminal, tmux killing its session, systemd's default
    KillMode=control-group. Measured: restarting the agent that way killed a running session's
    kernel outright, and the manager was left holding a RUNNING session with nothing behind it.
    """

    @pytest.fixture
    def spawner(self, runtime: RootlessOciRuntime, monkeypatch: pytest.MonkeyPatch) -> Any:
        """The real `create_task` spawn, with only the parts that need a live container stubbed."""
        monkeypatch.setattr(runtime, "_launch_argv", lambda *a, **k: ["sleep", "30"])
        monkeypatch.setattr(runtime, "_uid_drop_prefix", list)
        monkeypatch.setattr(runtime, "_write_seccomp", lambda *a, **k: None)

        async def _ready(proc: Any, gate_dir: Path, container_id: str) -> None:
            return None

        async def _child(proc: Any) -> int:
            return int(proc.pid)

        async def _hostname(pid: int, hostname: str | None) -> None:
            return None

        monkeypatch.setattr(runtime, "_wait_ready", _ready)
        monkeypatch.setattr(runtime, "_find_netns_child", _child)
        monkeypatch.setattr(runtime, "_set_hostname", _hostname)
        runtime._specs["c1"] = {}
        return runtime

    async def test_the_launch_lands_in_its_own_session(self, spawner: Any) -> None:
        """`setsid`, observed on the real spawned process rather than on the argv that asked for
        it. A different session id is exactly what puts the kernel out of reach of a signal sent
        to the agent's process group."""
        handle = await spawner.create_task("c1")
        try:
            assert os.getsid(handle.pid) != os.getsid(0)
            assert os.getpgid(handle.pid) != os.getpgid(0)
        finally:
            await spawner._reap("c1")

    async def test_without_it_a_child_shares_the_agents_group(self) -> None:
        """The control. Without this the assertion above would pass on any spawn at all — and the
        default really is to inherit, which is how the kernel came to die with its agent."""
        proc = await asyncio.create_subprocess_exec(
            "sleep", "30", stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL
        )
        try:
            assert os.getsid(proc.pid) == os.getsid(0)
            assert os.getpgid(proc.pid) == os.getpgid(0)
        finally:
            proc.kill()
            await proc.wait()

    async def test_reaping_still_reaches_the_detached_kernel(self, spawner: Any) -> None:
        """Detaching must not cost the agent its ability to stop the kernel: `_reap` and `_signal`
        address the pid, never the group, so a new session changes nothing for them."""
        handle = await spawner.create_task("c1")
        pid = handle.pid

        await spawner._reap("c1")

        with pytest.raises(ProcessLookupError):
            for _ in range(50):
                os.kill(pid, 0)
                await asyncio.sleep(0.02)
