"""The Docker two-phase start gate.

``docker create`` gives no PID and no netns, and ``docker start`` creates the netns and execs the
command in one step — so the attach has nowhere to go unless the container is held. These cover the
parts that decide *what* Docker is asked to run; that the container actually parks, that a veth
moved in while it waits is visible to the command afterwards, and that the PID does not change
across the release were measured against Docker 29.1.3 (see the module docstring).
"""

from __future__ import annotations

import os
import stat
from pathlib import Path
from typing import Any

from ai.backend.agent.docker.gate import GATE_WRAPPER, apply_gate, stage_gate
from ai.backend.agent.gate import GATE_MNT, GO_FIFO, PAUSE_SCRIPT_NAME, READY_MARKER


class TestStagingTheGate:
    def test_the_wrapper_is_executable(self, tmp_path: Path) -> None:
        stage_gate(tmp_path / "gate")
        script = tmp_path / "gate" / PAUSE_SCRIPT_NAME
        assert script.is_file()
        assert script.stat().st_mode & stat.S_IXUSR

    def test_the_fifo_exists(self, tmp_path: Path) -> None:
        # A regular file here would let the wrapper's read return immediately, and the container
        # would run its command before anything was attached — the exact failure this prevents.
        stage_gate(tmp_path / "gate")
        assert stat.S_ISFIFO((tmp_path / "gate" / GO_FIFO).stat().st_mode)

    def test_staging_twice_is_safe(self, tmp_path: Path) -> None:
        # A restart re-stages over its own leftovers; mkfifo on an existing path would raise.
        stage_gate(tmp_path / "gate")
        stage_gate(tmp_path / "gate")

    def test_the_wrapper_execs_its_arguments(self) -> None:
        # `exec "$@"` in place is what keeps the PID the agent attached to; a plain call would
        # leave the wrapper as PID 1 and put the user's process somewhere the attach never saw.
        assert 'exec "$@"' in GATE_WRAPPER
        assert f"{GATE_MNT}/{READY_MARKER}" in GATE_WRAPPER
        assert f"{GATE_MNT}/{GO_FIFO}" in GATE_WRAPPER


class TestApplyingTheGateToAContainerConfig:
    def test_the_entrypoint_becomes_the_wrapper(self, tmp_path: Path) -> None:
        config: dict[str, Any] = {"Image": "img:1", "Cmd": ["/opt/kernel/entrypoint.sh"]}
        apply_gate(config, tmp_path / "gate")
        assert config["Entrypoint"] == [f"{GATE_MNT}/{PAUSE_SCRIPT_NAME}"]

    def test_the_command_is_left_alone(self, tmp_path: Path) -> None:
        # Whatever Docker would have run becomes the wrapper's arguments; rewriting Cmd here would
        # silently change what the kernel starts.
        config: dict[str, Any] = {"Image": "img:1", "Cmd": ["a", "b"]}
        apply_gate(config, tmp_path / "gate")
        assert config["Cmd"] == ["a", "b"]

    def test_the_gate_is_bound_in(self, tmp_path: Path) -> None:
        gate_dir = tmp_path / "gate"
        config: dict[str, Any] = {"Image": "img:1"}
        apply_gate(config, gate_dir)
        assert f"{gate_dir}:{GATE_MNT}:rw" in config["HostConfig"]["Binds"]

    def test_existing_binds_survive(self, tmp_path: Path) -> None:
        # The backend has already put the scratch and the vfolders here; dropping them would start
        # a kernel with no home directory.
        config: dict[str, Any] = {"HostConfig": {"Binds": ["/scratch:/home/work:rw"]}}
        apply_gate(config, tmp_path / "gate")
        assert "/scratch:/home/work:rw" in config["HostConfig"]["Binds"]
        assert len(config["HostConfig"]["Binds"]) == 2

    def test_it_returns_the_same_object(self, tmp_path: Path) -> None:
        config: dict[str, Any] = {"Image": "img:1"}
        assert apply_gate(config, tmp_path / "gate") is config

    def test_the_bound_path_is_the_one_that_was_staged(self, tmp_path: Path) -> None:
        # The wrapper reads the FIFO by its in-container path, so the bind source must be the
        # directory the FIFO was actually made in.
        gate_dir = tmp_path / "gate"
        stage_gate(gate_dir)
        config: dict[str, Any] = {"Image": "img:1"}
        apply_gate(config, gate_dir)
        source = config["HostConfig"]["Binds"][0].split(":")[0]
        assert os.path.exists(Path(source) / GO_FIFO)
