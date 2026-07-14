"""Terminal-log persistence and stat-mode selection for the containerd agent.

Two Docker-parity gaps the manager can observe: a terminated kernel's logs must be collected before
the shim log file is unlinked, and per-container stats must be read from cgroups (there is no Docker
daemon to query — the config default 'docker' mode would 404 for every containerd container).
"""

from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast

import pytest

import ai.backend.agent.containerd.agent as agent_mod
import ai.backend.agent.containerd.runtime.grpc as grpc_mod
from ai.backend.agent.containerd.agent import ContainerdAgent, _read_container_log
from ai.backend.agent.stats import StatModes


@pytest.fixture
def log_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    root = tmp_path / "containerd-logs"
    root.mkdir()
    monkeypatch.setattr(grpc_mod, "CONTAINER_LOG_ROOT", root)
    return root


async def _drain(gen: Any) -> bytes:
    out = bytearray()
    async for chunk in gen:
        out += chunk
    return bytes(out)


class TestReadContainerLog:
    async def test_reads_the_whole_shim_log(self, log_root: Path) -> None:
        (log_root / "c1.log").write_bytes(b"line one\nline two\n")
        assert await _drain(_read_container_log("c1")) == b"line one\nline two\n"

    async def test_reads_a_log_larger_than_one_chunk(self, log_root: Path) -> None:
        payload = b"x" * (600 * 1024)  # spans several _LOG_READ_CHUNK reads
        (log_root / "c1.log").write_bytes(payload)
        assert await _drain(_read_container_log("c1")) == payload

    async def test_absent_log_yields_nothing(self, log_root: Path) -> None:
        # a task that wrote no log, or whose file is already gone, is not an error
        assert await _drain(_read_container_log("never-ran")) == b""


class TestCleanKernelCollectsLogs:
    """clean_kernel must persist the terminated kernel's logs before remove_container unlinks the
    shim log file, so the manager can still fetch a dead kernel's logs."""

    def _agent(self, events: list[str], monkeypatch: pytest.MonkeyPatch) -> ContainerdAgent:
        agent = ContainerdAgent.__new__(ContainerdAgent)

        async def collect_logs(kernel_id: Any, container_id: str, it: Any) -> None:
            events.append("collect_logs")

        async def remove_container(container_id: str) -> None:
            events.append("network.remove_container")

        monkeypatch.setattr(agent, "collect_logs", collect_logs, raising=False)
        agent._session_network = cast(Any, SimpleNamespace(remove_container=remove_container))
        agent._port_forwarder = cast(Any, SimpleNamespace(remove_container=_async_return([])))
        agent.kernel_registry = cast(Any, {})
        agent.port_pool = cast(Any, SimpleNamespace(release_many=lambda ports: None))
        agent.local_config = cast(
            Any,
            SimpleNamespace(
                container=SimpleNamespace(
                    scratch_root=Path("/nonexistent-scratch"), scratch_type=None
                ),
                debug=SimpleNamespace(skip_container_deletion=False),
            ),
        )
        return agent

    async def test_logs_collected_before_container_removed(
        self, log_root: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        (log_root / "kid.log").write_bytes(b"hello\n")
        events: list[str] = []
        agent = self._agent(events, monkeypatch)
        await agent.clean_kernel(cast(Any, "kid"), cast(Any, "kid"), restarting=False)
        assert events.index("collect_logs") < events.index("network.remove_container")

    async def test_restart_skips_log_collection(
        self, log_root: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # a restart reuses the container; its logs are not final yet and must not be collected
        events: list[str] = []
        agent = self._agent(events, monkeypatch)
        await agent.clean_kernel(cast(Any, "kid"), cast(Any, "kid"), restarting=True)
        assert "collect_logs" not in events

    async def test_second_clean_after_removal_does_not_recollect(
        self, log_root: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # clean_kernel can fire twice; the first collects and (via remove) unlinks the shim log.
        # The second must NOT collect — collect_logs always emits a sync event, so an empty
        # re-collect would overwrite the good log the first clean persisted.
        events: list[str] = []
        agent = self._agent(events, monkeypatch)
        # no shim log file on disk (already removed by a prior clean)
        assert not (log_root / "kid.log").exists()
        await agent.clean_kernel(cast(Any, "kid"), cast(Any, "kid"), restarting=False)
        assert "collect_logs" not in events


def _async_return(value: Any) -> Any:
    async def _fn(*a: Any, **k: Any) -> Any:
        return value

    return _fn


class TestCgroupPath:
    """Where the stats reader looks for a kernel's cgroup. The controller matters on v1: each has
    its own mount point, while the v2 unified tree holds them all at one root. Ignoring it (and
    assuming v2) made every read on a v1 host land on a path that does not exist — utilization
    silently absent for the life of the node."""

    def _agent(self, monkeypatch: pytest.MonkeyPatch, *, version: str) -> ContainerdAgent:
        agent = ContainerdAgent.__new__(ContainerdAgent)
        monkeypatch.setattr(agent, "get_cgroup_version", lambda: version)
        return agent

    def test_v2_reads_the_unified_hierarchy(self, monkeypatch: pytest.MonkeyPatch) -> None:
        agent = self._agent(monkeypatch, version="2")
        path = agent.get_cgroup_path("memory", "kern-1")
        assert path == Path("/sys/fs/cgroup/backend-ai/kern-1")

    def test_v1_reads_the_controllers_own_hierarchy(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(
            agent_mod, "get_cgroup_mount_point", lambda v, c: Path(f"/sys/fs/cgroup/{c}")
        )
        agent = self._agent(monkeypatch, version="1")

        assert agent.get_cgroup_path("memory", "kern-1") == Path(
            "/sys/fs/cgroup/memory/backend-ai/kern-1"
        )
        assert agent.get_cgroup_path("cpuacct", "kern-1") == Path(
            "/sys/fs/cgroup/cpuacct/backend-ai/kern-1"
        )

    def test_a_missing_v1_hierarchy_does_not_raise(self, monkeypatch: pytest.MonkeyPatch) -> None:
        # The stats readers resolve the path OUTSIDE the try that guards the read, so raising here
        # would abort the measurement round for every container on the node. A path that does not
        # exist is what they already know how to handle.
        def no_such_hierarchy(version: str, controller: str) -> Path:
            raise RuntimeError("could not find the cgroup mount point")

        monkeypatch.setattr(agent_mod, "get_cgroup_mount_point", no_such_hierarchy)
        agent = self._agent(monkeypatch, version="1")

        assert agent.get_cgroup_path("blkio", "kern-1") == Path("/sys/fs/cgroup/backend-ai/kern-1")


class TestEnumerateContainerPids:
    """Per-process stats must enumerate PIDs from the cgroup, not the (absent) Docker daemon."""

    def _agent(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, *, version: str = "2"
    ) -> ContainerdAgent:
        agent = ContainerdAgent.__new__(ContainerdAgent)
        cgroup_dir = tmp_path / "cg"
        cgroup_dir.mkdir()
        monkeypatch.setattr(agent, "get_cgroup_path", lambda controller, cid: cgroup_dir)
        monkeypatch.setattr(agent, "get_cgroup_version", lambda: version)
        self._cgroup_dir = cgroup_dir
        return agent

    async def test_reads_pids_from_cgroup_procs(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        agent = self._agent(tmp_path, monkeypatch)
        (self._cgroup_dir / "cgroup.procs").write_text("101\n102\n2003\n")
        assert await agent.enumerate_container_pids(cast(Any, "cid")) == [101, 102, 2003]

    async def test_missing_cgroup_yields_no_pids(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # the container has exited; its cgroup is gone -> empty, not an error
        agent = self._agent(tmp_path, monkeypatch)
        assert await agent.enumerate_container_pids(cast(Any, "cid")) == []

    async def test_non_numeric_lines_are_skipped(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        agent = self._agent(tmp_path, monkeypatch)
        (self._cgroup_dir / "cgroup.procs").write_text("101\n\ngarbage\n102\n")
        assert await agent.enumerate_container_pids(cast(Any, "cid")) == [101, 102]


class TestStatModeSelection:
    """The containerd backend must never use the daemon-querying 'docker' stat mode."""

    def _agent(self) -> ContainerdAgent:
        return ContainerdAgent.__new__(ContainerdAgent)

    def _config(self, stats_type: StatModes | None) -> Any:
        return cast(
            Any,
            SimpleNamespace(
                container=SimpleNamespace(
                    stats_type=SimpleNamespace(value=stats_type.value) if stats_type else None
                )
            ),
        )

    def test_forces_cgroup_even_when_config_says_docker(self) -> None:
        # 'docker' is the config default and is meaningful only for the Docker backend
        assert self._agent()._resolve_stat_mode(self._config(StatModes.DOCKER)) is StatModes.CGROUP

    def test_forces_cgroup_when_unset(self) -> None:
        assert self._agent()._resolve_stat_mode(self._config(None)) is StatModes.CGROUP

    def test_keeps_cgroup_when_explicitly_configured(self) -> None:
        assert self._agent()._resolve_stat_mode(self._config(StatModes.CGROUP)) is StatModes.CGROUP
