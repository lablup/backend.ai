"""Container logs left behind by an agent that died before it could clean up.

`remove_container` is the only thing that unlinks a log, and it only runs while the agent is alive
to run it. The rotation loop keeps an orphan *capped* — it globs the log root by design — but capped
is not removed, and nothing else ever comes back for it. Measured on the testbed: four and five logs
from kernels of two days earlier, on nodes with no session running.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from ai.backend.agent.containerd.logs import rotated_paths
from ai.backend.agent.rootless import base
from ai.backend.agent.rootless.base import RootlessOciRuntime


@pytest.fixture
def log_root(runtime: RootlessOciRuntime, tmp_path: Path) -> Path:
    root = tmp_path / "container-logs"
    root.mkdir()
    runtime._log_root = root
    return root


def _log(root: Path, container_id: str, *, rotated: int = 0) -> Path:
    active = root / f"{container_id}.log"
    active.write_text("output")
    for i in range(1, rotated + 1):
        rotated_paths(active)[i].write_text("older output")
    return active


def _no_cgroups(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """No cgroup for any id — the state of a node whose kernels are all gone."""
    monkeypatch.setattr(base, "container_cgroup_fs_path", lambda cid: tmp_path / "nocgroup" / cid)


class TestWhatIsRemoved:
    def test_a_log_with_no_container_behind_it(
        self,
        runtime: RootlessOciRuntime,
        log_root: Path,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        _no_cgroups(monkeypatch, tmp_path)
        active = _log(log_root, "dead")

        runtime._sweep_orphan_logs()

        assert not active.exists()

    def test_its_rotated_siblings_go_too(
        self,
        runtime: RootlessOciRuntime,
        log_root: Path,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        """They are as much the kernel's log as the active file; leaving them leaks most of it."""
        _no_cgroups(monkeypatch, tmp_path)
        active = _log(log_root, "dead", rotated=4)

        runtime._sweep_orphan_logs()

        assert [p for p in rotated_paths(active) if p.exists()] == []


class TestWhatIsLeftAlone:
    def test_a_container_the_journal_replay_recovered(
        self,
        runtime: RootlessOciRuntime,
        log_root: Path,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        _no_cgroups(monkeypatch, tmp_path)
        active = _log(log_root, "alive")
        runtime._pids["alive"] = 4242

        runtime._sweep_orphan_logs()

        assert active.exists()

    def test_a_container_whose_cgroup_still_has_processes(
        self,
        runtime: RootlessOciRuntime,
        log_root: Path,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        """The second signal, for a live container whose journal entry was lost: `_pids` does not
        know it, but its processes are still in its cgroup."""
        cgroup = tmp_path / "cgroup" / "running"
        cgroup.mkdir(parents=True)
        (cgroup / "cgroup.procs").write_text("4242\n")
        monkeypatch.setattr(base, "container_cgroup_fs_path", lambda cid: tmp_path / "cgroup" / cid)
        active = _log(log_root, "running")

        runtime._sweep_orphan_logs()

        assert active.exists()

    def test_an_empty_cgroup_does_not_protect_it(
        self,
        runtime: RootlessOciRuntime,
        log_root: Path,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        """A cgroup the sweep above has not reclaimed yet is not evidence of a live container."""
        cgroup = tmp_path / "cgroup" / "dead"
        cgroup.mkdir(parents=True)
        (cgroup / "cgroup.procs").write_text("")
        monkeypatch.setattr(base, "container_cgroup_fs_path", lambda cid: tmp_path / "cgroup" / cid)
        active = _log(log_root, "dead")

        runtime._sweep_orphan_logs()

        assert not active.exists()

    def test_a_file_that_is_not_a_log(
        self,
        runtime: RootlessOciRuntime,
        log_root: Path,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        _no_cgroups(monkeypatch, tmp_path)
        other = log_root / "notes.txt"
        other.write_text("not ours")

        runtime._sweep_orphan_logs()

        assert other.exists()

    def test_no_log_root_configured_is_not_an_error(self, runtime: RootlessOciRuntime) -> None:
        """`configure_logging` has not run yet on a runtime opened for a one-off probe."""
        runtime._log_root = None

        runtime._sweep_orphan_logs()  # does not raise


class TestWhenItRuns:
    """It cannot run at `open()`: the log root is not known until `configure_logging`, and a sweep
    that finds no root to walk does nothing at all — silently. Measured live: an agent restarted
    with the sweep wired into `open()` left all four orphaned logs in place."""

    def test_configure_logging_is_what_triggers_it(
        self, runtime: RootlessOciRuntime, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        _no_cgroups(monkeypatch, tmp_path)
        root = tmp_path / "logs"
        root.mkdir()
        orphan = _log(root, "dead")

        runtime.configure_logging(tmp_path / "launcher", root, 10 * 1024 * 1024)

        assert not orphan.exists()

    def test_a_live_container_survives_that_call_too(
        self, runtime: RootlessOciRuntime, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        _no_cgroups(monkeypatch, tmp_path)
        root = tmp_path / "logs"
        root.mkdir()
        alive = _log(root, "alive")
        runtime._pids["alive"] = 4242

        runtime.configure_logging(tmp_path / "launcher", root, 10 * 1024 * 1024)

        assert alive.exists()
