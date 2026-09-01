"""What `enroot start` is actually invoked with.

This is the translation layer from the OCI spec the containerd agent builds to an enroot command
line, and it is where most of this backend's shipped bugs have been: the spec was read at the wrong
key so no environment reached the container at all; the GPU allowlist was left unpinned so every
kernel saw every GPU; `readonly` mounts were forwarded writable. None of those fail loudly — the
container starts fine and is simply wrong — so they are pinned here as argv assertions.
"""

from __future__ import annotations

import itertools
import os
from pathlib import Path
from typing import Any

import pytest

from ai.backend.agent.enroot.runtime import EnrootRuntime
from ai.backend.agent.rootless.base import DEFAULT_SHM_BYTES

_CID = "kernel-1"


@pytest.fixture
def gate_dir(tmp_path: Path) -> Path:
    return tmp_path / "gate"


def _argv(runtime: EnrootRuntime, gate_dir: Path, **spec: Any) -> list[str]:
    return runtime._launch_argv(_CID, spec, gate_dir)


def _env_of(argv: list[str]) -> dict[str, str]:
    """The `-e KEY=VAL` pairs, as a dict."""
    out: dict[str, str] = {}
    for flag, value in itertools.pairwise(argv):
        if flag == "-e":
            key, _, val = value.partition("=")
            out[key] = val
    return out


def _mounts_of(argv: list[str]) -> list[str]:
    return [value for flag, value in itertools.pairwise(argv) if flag == "-m"]


class TestEnvironment:
    def test_the_specs_env_reaches_the_container(
        self, runtime: EnrootRuntime, gate_dir: Path
    ) -> None:
        """The original bug: this read `spec["process"]["env"]`, a shape the agent never produces,
        so *nothing* was forwarded. Everything downstream still worked well enough to look healthy
        — the runner reads its own config from a mounted file — which is why it survived so long.
        The accelerator hooks, which run before the command and see only this, did not."""
        argv = _argv(runtime, gate_dir, env={"BACKENDAI_KERNEL_ID": "abc", "MY_VAR": "1"})

        env = _env_of(argv)
        assert env["BACKENDAI_KERNEL_ID"] == "abc"
        assert env["MY_VAR"] == "1"

    def test_a_multi_line_value_is_dropped(self, runtime: EnrootRuntime, gate_dir: Path) -> None:
        """enroot's env file is line-oriented, so an embedded newline does not corrupt just that
        variable — every variable after it shifts."""
        argv = _argv(runtime, gate_dir, env={"GOOD": "1", "BAD": "a\nb", "ALSO_GOOD": "2"})

        env = _env_of(argv)
        assert "BAD" not in env
        assert env["GOOD"] == "1"
        assert env["ALSO_GOOD"] == "2"

    def test_the_runner_is_forced_to_container_root(
        self, runtime: EnrootRuntime, gate_dir: Path
    ) -> None:
        """`--root` maps container-root to the host kernel uid, which owns the scratch. A non-zero
        LOCAL_USER_ID from the image base would leave the runner as a container uid that is
        unmapped in the rootless userns, i.e. `nobody`, unable to read the scratch it owns.

        The uid asked for here is the node's own kernel uid — what a UID_MATCH image gets — so
        container-root already lands on it and there is nothing this backend cannot honour. An id
        it cannot produce is refused instead; see tests/unit/agent/rootless/test_container_identity.
        """
        argv = _argv(
            runtime,
            gate_dir,
            env={"LOCAL_USER_ID": str(os.geteuid()), "LOCAL_GROUP_ID": str(os.getegid())},
        )

        env = _env_of(argv)
        assert env["LOCAL_USER_ID"] == "0"
        assert env["LOCAL_GROUP_ID"] == "0"


class TestGpuAllowlist:
    def test_only_the_allocated_gpus_are_visible(
        self, runtime: EnrootRuntime, gate_dir: Path
    ) -> None:
        argv = _argv(runtime, gate_dir, gpus=["0", "2"])

        env = _env_of(argv)
        assert env["NVIDIA_VISIBLE_DEVICES"] == "0,2"
        assert env["NVIDIA_DRIVER_CAPABILITIES"] == "all"

    def test_a_cpu_only_kernel_gets_no_device(self, runtime: EnrootRuntime, gate_dir: Path) -> None:
        """`void` is the hook's own no-op sentinel. Leaving the variable unset instead lets the
        hook fall back to `all` on a GPU node — a CPU-only kernel with every GPU attached."""
        argv = _argv(runtime, gate_dir, gpus=[])

        assert _env_of(argv)["NVIDIA_VISIBLE_DEVICES"] == "void"

    def test_the_allocation_overrides_what_the_image_asked_for(
        self, runtime: EnrootRuntime, gate_dir: Path
    ) -> None:
        """CUDA base images set NVIDIA_VISIBLE_DEVICES=all in their own config. The scheduler's
        allocation is the authoritative one and must win."""
        argv = _argv(runtime, gate_dir, env={"NVIDIA_VISIBLE_DEVICES": "all"}, gpus=["1"])

        assert _env_of(argv)["NVIDIA_VISIBLE_DEVICES"] == "1"


class TestMounts:
    def test_a_readonly_mount_is_forwarded_readonly(
        self, runtime: EnrootRuntime, gate_dir: Path
    ) -> None:
        """Two spellings reach here: `readonly` from the runtime-neutral descriptor, and `ro` in
        `options` from the OCI runtime-spec. Honouring only one hands the kernel a writable krunner
        and writable read-only vfolders."""
        argv = _argv(
            runtime,
            gate_dir,
            mounts=[
                {"source": "/host/a", "destination": "/a", "type": "bind", "readonly": True},
                {"source": "/host/b", "destination": "/b", "type": "bind", "options": ["ro"]},
                {"source": "/host/c", "destination": "/c", "type": "bind"},
            ],
        )

        mounts = _mounts_of(argv)
        assert "/host/a:/a:none:x-create=auto,bind,ro" in mounts
        assert "/host/b:/b:none:x-create=auto,bind,ro" in mounts
        assert "/host/c:/c:none:x-create=auto,bind,rw" in mounts

    def test_pseudo_filesystems_are_not_forwarded(
        self, runtime: EnrootRuntime, gate_dir: Path
    ) -> None:
        """enroot builds proc/sys/dev itself for the userns; bind-mounting the host's over them
        would undo the isolation the userns just bought."""
        argv = _argv(
            runtime,
            gate_dir,
            mounts=[
                {"source": "proc", "destination": "/proc", "type": "proc"},
                {"source": "sysfs", "destination": "/sys", "type": "sysfs"},
                {"source": "cgroup", "destination": "/sys/fs/cgroup", "type": "cgroup2"},
                {"source": "/host/real", "destination": "/real", "type": "bind"},
            ],
        )

        mounts = _mounts_of(argv)
        assert not [m for m in mounts if m.startswith(("proc:", "sysfs:", "cgroup:"))]
        assert "/host/real:/real:none:x-create=auto,bind,rw" in mounts

    def test_an_incomplete_mount_is_skipped(self, runtime: EnrootRuntime, gate_dir: Path) -> None:
        argv = _argv(
            runtime,
            gate_dir,
            mounts=[{"source": "/host/a"}, {"destination": "/b"}, {}],
        )

        assert not [m for m in _mounts_of(argv) if "/host/a" in m or ":/b:" in m]

    def test_device_nodes_are_bind_mounted(self, runtime: EnrootRuntime, gate_dir: Path) -> None:
        """runc grants devices through the device cgroup, but a rootless userns cannot mknod — so
        the already-created host node is bound in, which is all it needs."""
        argv = _argv(
            runtime,
            gate_dir,
            devices=[
                {"source": "/dev/kfd"},
                {"source": "/dev/dri/renderD128", "destination": "/dev/dri/renderD128"},
            ],
        )

        mounts = _mounts_of(argv)
        assert "/dev/kfd:/dev/kfd:none:x-create=auto,bind,rw" in mounts
        assert "/dev/dri/renderD128:/dev/dri/renderD128:none:x-create=auto,bind,rw" in mounts


class TestDevShm:
    def _shm(self, argv: list[str]) -> str:
        (entry,) = [m for m in _mounts_of(argv) if ":/dev/shm:" in m]
        return entry

    def test_each_kernel_gets_its_own_sized_shm(
        self, runtime: EnrootRuntime, gate_dir: Path
    ) -> None:
        """enroot's default fstab BINDS the host /dev/shm into every container, so every kernel on
        the node would share one — visible segments and a shared size budget."""
        argv = _argv(runtime, gate_dir, shmem=2 * 1024**3)

        entry = self._shm(argv)
        assert entry.startswith("tmpfs:/dev/shm:tmpfs:")
        assert "size=2147483648" in entry

    def test_it_falls_back_to_dockers_default(self, runtime: EnrootRuntime, gate_dir: Path) -> None:
        assert f"size={DEFAULT_SHM_BYTES}" in self._shm(_argv(runtime, gate_dir))

    def test_it_is_declared_after_the_gate_so_it_wins(
        self, runtime: EnrootRuntime, gate_dir: Path
    ) -> None:
        """Later -m entries override earlier ones, which is how this beats the default fstab."""
        argv = _argv(runtime, gate_dir)
        mounts = _mounts_of(argv)

        assert mounts.index(self._shm(argv)) > 0


class TestNamespacesAndCommand:
    def test_the_namespaces_enroot_is_asked_for(
        self, runtime: EnrootRuntime, gate_dir: Path
    ) -> None:
        """`--uts` carries the kernel's own cluster hostname. `--ipc` is deliberately absent: it
        makes enroot's `10-devices` hook rebuild /dev, and that hook binds /dev/log with no
        `nofail`, so it hard-fails on any host without a syslog socket — every containerised
        agent."""
        argv = _argv(runtime, gate_dir)

        assert argv[:2] == ["enroot", "start"]
        for flag in ("--root", "--net", "--pid", "--uts", "--rw"):
            assert flag in argv
        assert "--ipc" not in argv

    def test_the_real_command_follows_the_pause_wrapper(
        self, runtime: EnrootRuntime, gate_dir: Path
    ) -> None:
        """The two-phase gate: enroot's command is the wrapper and the kernel entrypoint is its
        args, so the exec preserves the PID the network layer already attached to."""
        runtime._commands[_CID] = ["/opt/kernel/entrypoint.sh", "--debug"]

        argv = _argv(runtime, gate_dir)

        assert argv[-4:] == [
            _CID,
            "/.bai-rootless-gate/pause.sh",
            "/opt/kernel/entrypoint.sh",
            "--debug",
        ]

    def test_the_gate_is_mounted_where_the_wrapper_expects_it(
        self, runtime: EnrootRuntime, gate_dir: Path
    ) -> None:
        argv = _argv(runtime, gate_dir)

        assert f"{gate_dir}:/.bai-rootless-gate:none:x-create=auto,bind,rw" in _mounts_of(argv)
