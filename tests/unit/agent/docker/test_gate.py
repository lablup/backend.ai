"""The Docker two-phase start gate: what Docker is asked to run so the container parks before
its command. Parking, veth visibility and PID stability were measured on Docker 29.1.3."""

from __future__ import annotations

import asyncio
import os
import stat
from pathlib import Path
from typing import Any

from ai.backend.agent.docker.gate import GATE_WRAPPER, apply_gate, stage_gate
from ai.backend.agent.gate import GATE_MNT, GO_FIFO, PAUSE_SCRIPT_NAME, READY_MARKER, signal_go


class TestStagingTheGate:
    def test_the_wrapper_is_executable(self, tmp_path: Path) -> None:
        stage_gate(tmp_path / "gate")
        script = tmp_path / "gate" / PAUSE_SCRIPT_NAME
        assert script.is_file()
        assert script.stat().st_mode & stat.S_IXUSR

    def test_the_fifo_exists(self, tmp_path: Path) -> None:
        # A regular file would let the wrapper's read return and run the command before attach.
        stage_gate(tmp_path / "gate")
        assert stat.S_ISFIFO((tmp_path / "gate" / GO_FIFO).stat().st_mode)

    def test_staging_twice_is_safe(self, tmp_path: Path) -> None:
        # A restart re-stages over its own leftovers; mkfifo on an existing path would raise.
        stage_gate(tmp_path / "gate")
        stage_gate(tmp_path / "gate")

    async def test_the_wrapper_parks_then_execs_its_command_in_place(self, tmp_path: Path) -> None:
        # The agent attaches to the parked PID, so the command must run under that same PID.
        gate_dir = tmp_path / "gate"
        stage_gate(gate_dir)
        script = tmp_path / "wrapper.sh"
        script.write_text(GATE_WRAPPER.replace(GATE_MNT, str(gate_dir)))
        proc = await asyncio.create_subprocess_exec(
            "sh", str(script), "sh", "-c", "echo $$", stdout=asyncio.subprocess.PIPE
        )
        for _ in range(100):
            if (gate_dir / READY_MARKER).exists():
                break
            await asyncio.sleep(0.05)
        assert (gate_dir / READY_MARKER).exists()
        assert proc.returncode is None, "the command ran before the gate was released"
        assert await asyncio.to_thread(signal_go, gate_dir)
        stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=5)
        assert stdout.decode().strip() == str(proc.pid)


class TestApplyingTheGateToAContainerConfig:
    def test_the_entrypoint_becomes_the_wrapper(self, tmp_path: Path) -> None:
        config: dict[str, Any] = {"Image": "img:1", "Cmd": ["/opt/kernel/entrypoint.sh"]}
        apply_gate(config, tmp_path / "gate")
        assert config["Entrypoint"] == [f"{GATE_MNT}/{PAUSE_SCRIPT_NAME}"]

    def test_the_command_is_left_alone(self, tmp_path: Path) -> None:
        # Cmd becomes the wrapper's arguments unchanged.
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

    def test_the_bound_path_is_the_one_that_was_staged(self, tmp_path: Path) -> None:
        # The wrapper reads the FIFO by its in-container path, so the bind source must be the
        # directory the FIFO was actually made in.
        gate_dir = tmp_path / "gate"
        stage_gate(gate_dir)
        config: dict[str, Any] = {"Image": "img:1"}
        apply_gate(config, gate_dir)
        source = config["HostConfig"]["Binds"][0].split(":")[0]
        assert os.path.exists(Path(source) / GO_FIFO)
