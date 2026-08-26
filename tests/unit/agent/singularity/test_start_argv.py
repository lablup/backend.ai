"""What `apptainer exec` is actually invoked with.

The flags here are not interchangeable with enroot's, and the differences were established by
measurement rather than from the manual — each one below records a result that would otherwise be
an easy, silent mistake. None of them fail loudly: the container starts either way and is simply
less isolated than it claims.
"""

from __future__ import annotations

import itertools
from pathlib import Path
from typing import Any

import pytest

from ai.backend.agent.singularity.runtime import SingularityRuntime

_CID = "kernel-1"


@pytest.fixture
def gate_dir(tmp_path: Path) -> Path:
    return tmp_path / "gate"


def _argv(runtime: SingularityRuntime, gate_dir: Path, **spec: Any) -> list[str]:
    return runtime._launch_argv(_CID, spec, gate_dir)


def _env_of(argv: list[str]) -> dict[str, str]:
    out: dict[str, str] = {}
    for flag, value in itertools.pairwise(argv):
        if flag == "--env":
            key, _, val = value.partition("=")
            out[key] = val
    return out


def _binds_of(argv: list[str]) -> list[str]:
    return [value for flag, value in itertools.pairwise(argv) if flag == "--bind"]


class TestIsolationFlags:
    def test_contain_is_always_present(self, runtime: SingularityRuntime, gate_dir: Path) -> None:
        """The single most important flag. Without `--contain` apptainer binds the host's /dev
        wholesale, so a CPU-only kernel on a GPU node sees every /dev/nvidia* even though no GPU
        flag was passed at all — measured. It also gives the container its own /dev/shm."""
        assert "--contain" in _argv(runtime, gate_dir)

    def test_a_private_loopback_only_netns(
        self, runtime: SingularityRuntime, gate_dir: Path
    ) -> None:
        """`--network none` is what makes `--net` usable unprivileged, and it is also what we want:
        the agent (or the privnet) builds the data plane, never the runtime."""
        argv = _argv(runtime, gate_dir)

        assert "--net" in argv
        assert argv[argv.index("--network") + 1] == "none"

    def test_container_root_maps_to_the_kernel_uid(
        self, runtime: SingularityRuntime, gate_dir: Path
    ) -> None:
        assert "--fakeroot" in _argv(runtime, gate_dir)

    def test_its_own_uts_and_pid_namespaces(
        self, runtime: SingularityRuntime, gate_dir: Path
    ) -> None:
        argv = _argv(runtime, gate_dir)

        assert "--uts" in argv
        assert "--pid" in argv

    def test_the_environment_starts_empty(
        self, runtime: SingularityRuntime, gate_dir: Path
    ) -> None:
        """Without `--cleanenv` the agent pod's own environment reaches the container — and a
        GPU-enabled fatPod sets NVIDIA_VISIBLE_DEVICES=all to get the driver injected into
        *itself*, which would hand every device to every kernel."""
        assert "--cleanenv" in _argv(runtime, gate_dir)


class TestOverlay:
    def test_writes_go_to_the_containers_own_overlay(
        self, runtime: SingularityRuntime, gate_dir: Path
    ) -> None:
        """The image sandbox is shared and must stay read-only; two kernels of the same image
        would otherwise write over each other."""
        argv = _argv(runtime, gate_dir)

        overlay = argv[argv.index("--overlay") + 1]
        assert overlay == str(runtime._overlay_dir(_CID))

    def test_the_image_sandbox_is_the_last_positional_before_the_wrapper(
        self, runtime: SingularityRuntime, gate_dir: Path
    ) -> None:
        argv = _argv(runtime, gate_dir)

        assert argv[-3] == str(runtime._sandbox("registry/py:3.12"))


class TestGpuGating:
    def test_an_allocated_gpu_goes_through_nvccli(
        self, runtime: SingularityRuntime, gate_dir: Path
    ) -> None:
        """`--nvccli` drives the same nvidia-container-cli enroot's hook uses, so the allocation is
        enforced by device injection. `--nv` — the flag everyone reaches for — IGNORES
        NVIDIA_VISIBLE_DEVICES entirely and injects every device on the node (measured)."""
        argv = _argv(runtime, gate_dir, gpus=["0", "2"])

        assert "--nvccli" in argv
        assert "--nv" not in argv
        assert _env_of(argv)["NVIDIA_VISIBLE_DEVICES"] == "0,2"

    def test_a_cpu_only_kernel_asks_for_no_gpu_at_all(
        self, runtime: SingularityRuntime, gate_dir: Path
    ) -> None:
        """There is no sentinel to pass: apptainer rejects enroot's `void`/`none` outright with
        `unknown device`. "No GPU" is the *absence* of the flag, and `--contain` is what keeps the
        host's device nodes out."""
        argv = _argv(runtime, gate_dir, gpus=[])

        assert "--nvccli" not in argv
        assert "NVIDIA_VISIBLE_DEVICES" not in _env_of(argv)

    def test_the_images_own_gpu_request_is_overridden(
        self, runtime: SingularityRuntime, gate_dir: Path
    ) -> None:
        """CUDA base images set NVIDIA_VISIBLE_DEVICES=all in their config; the scheduler's
        allocation is the authoritative one."""
        argv = _argv(runtime, gate_dir, env={"NVIDIA_VISIBLE_DEVICES": "all"}, gpus=["1"])

        assert _env_of(argv)["NVIDIA_VISIBLE_DEVICES"] == "1"

    def test_a_stale_allocation_is_not_left_behind_for_a_cpu_kernel(
        self, runtime: SingularityRuntime, gate_dir: Path
    ) -> None:
        argv = _argv(runtime, gate_dir, env={"NVIDIA_VISIBLE_DEVICES": "all"}, gpus=[])

        assert "NVIDIA_VISIBLE_DEVICES" not in _env_of(argv)


class TestEnvironment:
    def test_the_specs_env_reaches_the_container(
        self, runtime: SingularityRuntime, gate_dir: Path
    ) -> None:
        argv = _argv(runtime, gate_dir, env={"BACKENDAI_KERNEL_ID": "abc", "MY_VAR": "1"})

        env = _env_of(argv)
        assert env["BACKENDAI_KERNEL_ID"] == "abc"
        assert env["MY_VAR"] == "1"

    def test_a_multi_line_value_is_dropped(
        self, runtime: SingularityRuntime, gate_dir: Path
    ) -> None:
        argv = _argv(runtime, gate_dir, env={"GOOD": "1", "BAD": "a\nb", "ALSO": "2"})

        env = _env_of(argv)
        assert "BAD" not in env
        assert env["GOOD"] == "1" and env["ALSO"] == "2"

    def test_the_runner_is_forced_to_container_root(
        self, runtime: SingularityRuntime, gate_dir: Path
    ) -> None:
        argv = _argv(runtime, gate_dir, env={"LOCAL_USER_ID": "1100"})

        env = _env_of(argv)
        assert env["LOCAL_USER_ID"] == "0"
        assert env["LOCAL_GROUP_ID"] == "0"


class TestMounts:
    def test_the_gate_is_bound_where_the_wrapper_expects_it(
        self, runtime: SingularityRuntime, gate_dir: Path
    ) -> None:
        argv = _argv(runtime, gate_dir)

        assert f"{gate_dir}:/.bai-rootless-gate:rw" in _binds_of(argv)
        assert argv[-2] == "/.bai-rootless-gate/pause.sh"

    def test_readonly_is_honoured_in_both_spellings(
        self, runtime: SingularityRuntime, gate_dir: Path
    ) -> None:
        argv = _argv(
            runtime,
            gate_dir,
            mounts=[
                {"source": "/h/a", "destination": "/a", "type": "bind", "readonly": True},
                {"source": "/h/b", "destination": "/b", "type": "bind", "options": ["ro"]},
                {"source": "/h/c", "destination": "/c", "type": "bind"},
            ],
        )

        binds = _binds_of(argv)
        assert "/h/a:/a:ro" in binds
        assert "/h/b:/b:ro" in binds
        assert "/h/c:/c:rw" in binds

    def test_pseudo_filesystems_are_not_forwarded(
        self, runtime: SingularityRuntime, gate_dir: Path
    ) -> None:
        argv = _argv(
            runtime,
            gate_dir,
            mounts=[
                {"source": "proc", "destination": "/proc", "type": "proc"},
                {"source": "cgroup", "destination": "/sys/fs/cgroup", "type": "cgroup2"},
                {"source": "/h/real", "destination": "/real", "type": "bind"},
            ],
        )

        binds = _binds_of(argv)
        assert not [b for b in binds if b.startswith(("proc:", "cgroup:"))]
        assert "/h/real:/real:rw" in binds

    def test_devices_are_bound_back_in(self, runtime: SingularityRuntime, gate_dir: Path) -> None:
        """`--contain` gives a minimal /dev, so anything an accelerator plugin asked for has to be
        put back explicitly."""
        argv = _argv(runtime, gate_dir, devices=[{"source": "/dev/kfd"}])

        assert "/dev/kfd:/dev/kfd:rw" in _binds_of(argv)


class TestCommand:
    def test_the_real_command_follows_the_pause_wrapper(
        self, runtime: SingularityRuntime, gate_dir: Path
    ) -> None:
        """The two-phase gate: apptainer's command is the wrapper and the kernel entrypoint is its
        args, so the exec preserves the host PID the network layer attached to (measured)."""
        runtime._commands[_CID] = ["/opt/kernel/entrypoint.sh", "--debug"]

        argv = _argv(runtime, gate_dir)

        assert argv[-2:] == ["/opt/kernel/entrypoint.sh", "--debug"]
        assert argv[:2] == [runtime._binary, "exec"]


class TestGpuAllocationReachesNvccli:
    """``--nvccli`` builds its nvidia-container-cli call from **apptainer's own** environment.

    The shared rootless base strips ``NVIDIA_*`` from the runtime's process environment -- correct
    for enroot, whose hook reads the container's env file. Passing the allocation only through
    ``--env`` therefore injects nothing: measured, the container came up with `/dev/nvidiactl` and
    no `/dev/nvidia0`, `nvidia-smi` said "No devices were found" and `cuInit` returned 100.
    """

    def test_launch_env_carries_the_allocation(self, runtime: SingularityRuntime) -> None:
        env = runtime._launch_env({"gpus": ["0"]})
        assert env["NVIDIA_VISIBLE_DEVICES"] == "0"
        assert env["NVIDIA_DRIVER_CAPABILITIES"] == "compute,utility"

    def test_launch_env_is_empty_without_gpus(self, runtime: SingularityRuntime) -> None:
        # A CPU kernel must not get a stray NVIDIA_* in the runtime env: with --nvccli absent it
        # would do nothing, and with it present it would hand devices to a session that asked for
        # none.
        assert runtime._launch_env({}) == {}
        assert runtime._launch_env({"gpus": []}) == {}

    def test_capabilities_are_never_all(self, runtime: SingularityRuntime, gate_dir: Path) -> None:
        # apptainer validates this value and aborts the launch on anything it does not know:
        # `FATAL: container creation failed: unknown NVIDIA_DRIVER_CAPABILITIES value: all`.
        # nvidia-container-cli and the enroot hook do accept "all", which is why it is easy to
        # write here and only fails on this backend.
        assert "all" not in runtime._launch_env({"gpus": ["0"]})["NVIDIA_DRIVER_CAPABILITIES"]
        env = _env_of(_argv(runtime, gate_dir, gpus=["0"]))
        assert env.get("NVIDIA_DRIVER_CAPABILITIES") != "all"
