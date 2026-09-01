"""What `podman create` is told, which is the whole of how a session container is confined.

podman is configured entirely through its command line, so every guarantee this backend makes --
the container cannot run before the agent has attached, the netns is ours to fill, a read-only
vfolder is read-only, the kernel-runner can read the scratch it owns -- is a flag in this argv or
it does not exist.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import pytest

from ai.backend.agent.podman.runtime import PodmanRuntime
from ai.backend.agent.rootless.gate import GATE_MNT


@pytest.fixture
def runtime(tmp_path: Path) -> PodmanRuntime:
    return PodmanRuntime(
        data_path=tmp_path / "data",
        cache_path=tmp_path / "cache",
        runtime_path=tmp_path / "run",
        state_path=tmp_path / "state",
        kernel_uid=os.geteuid(),
        kernel_gid=os.getegid(),
    )


def _argv(
    runtime: PodmanRuntime, spec: dict[str, Any], command: list[str] | None = None
) -> list[str]:
    gate = runtime._gate_dir("c1")
    return runtime._create_argv("c1", "img:1", command or ["/bin/true"], spec, gate)


class TestTheGate:
    def test_the_wrapper_is_the_entrypoint_and_the_command_is_its_argument(
        self, runtime: PodmanRuntime
    ) -> None:
        """`podman start` execs immediately, so the user's command must not be the entrypoint --
        it has to sit behind the wrapper, which the agent releases only after attaching."""
        argv = _argv(runtime, {}, ["python", "-m", "runner"])

        entrypoint = argv[argv.index("--entrypoint") + 1]
        assert json.loads(entrypoint) == [f"{GATE_MNT}/pause.sh"]
        assert argv[-4:] == ["img:1", "python", "-m", "runner"]

    def test_the_gate_directory_is_mounted_where_the_wrapper_looks_for_it(
        self, runtime: PodmanRuntime
    ) -> None:
        argv = _argv(runtime, {})

        assert f"type=bind,src={runtime._gate_dir('c1')},dst={GATE_MNT},rw" in argv

    def test_the_container_gets_its_own_empty_netns(self, runtime: PodmanRuntime) -> None:
        """The privnet puts the veth in. A network podman set up itself would need netavark and
        would leave a second interface in the namespace."""
        assert "--network=none" in _argv(runtime, {})


class TestMounts:
    def test_a_read_only_mount_stays_read_only_in_both_spellings(
        self, runtime: PodmanRuntime
    ) -> None:
        """`readonly` is the runtime-neutral descriptor's spelling and `options` the OCI one;
        honouring one and not the other hands the kernel a writable krunner."""
        argv = _argv(
            runtime,
            {
                "mounts": [
                    {"source": "/host/a", "destination": "/a", "readonly": True},
                    {"source": "/host/b", "destination": "/b", "options": ["ro", "bind"]},
                    {"source": "/host/c", "destination": "/c"},
                ]
            },
        )

        assert "type=bind,src=/host/a,dst=/a,ro" in argv
        assert "type=bind,src=/host/b,dst=/b,ro" in argv
        assert "type=bind,src=/host/c,dst=/c,rw" in argv

    def test_what_the_userns_provides_itself_is_not_bind_mounted_from_the_host(
        self, runtime: PodmanRuntime
    ) -> None:
        argv = _argv(
            runtime,
            {"mounts": [{"source": "proc", "destination": "/proc", "type": "proc"}]},
        )

        assert not any("dst=/proc" in a for a in argv)

    def test_a_device_node_is_passed_through(self, runtime: PodmanRuntime) -> None:
        """A rootless userns cannot mknod, so an already-created host node is handed over instead
        -- this is how an AMD GPU, an NPU or an IB HCA reaches the container."""
        argv = _argv(runtime, {"devices": [{"source": "/dev/kfd"}]})

        assert "/dev/kfd:/dev/kfd:rwm" in argv


class TestTheKernelRunnersIdentity:
    def test_local_user_id_is_forced_to_container_root(self, runtime: PodmanRuntime) -> None:
        """Rootless podman maps container-root to the invoking uid, which owns the scratch. A
        non-zero LOCAL_USER_ID would be unmapped in that namespace and could not read it.

        The uid asked for here is the node's own kernel uid — what a UID_MATCH image gets — so
        container-root already lands on it. An id this backend cannot produce is refused instead;
        see tests/unit/agent/rootless/test_container_identity.
        """
        wanted = str(os.geteuid())
        argv = _argv(
            runtime, {"env": {"LOCAL_USER_ID": wanted, "LOCAL_GROUP_ID": str(os.getegid())}}
        )

        assert "LOCAL_USER_ID=0" in argv
        assert "LOCAL_GROUP_ID=0" in argv
        assert f"LOCAL_USER_ID={wanted}" not in argv

    def test_the_rest_of_the_environment_is_forwarded(self, runtime: PodmanRuntime) -> None:
        argv = _argv(runtime, {"env": {"BACKENDAI_KERNEL_ID": "k1"}})

        assert "BACKENDAI_KERNEL_ID=k1" in argv


class TestSeccomp:
    def test_a_compiled_profile_is_handed_to_podman(self, runtime: PodmanRuntime) -> None:
        argv = _argv(runtime, {"seccomp": {"defaultAction": "SCMP_ACT_ALLOW"}})

        opt = next(a for a in argv if a.startswith("seccomp="))
        written = json.loads(Path(opt.removeprefix("seccomp=")).read_text())
        assert written == {"defaultAction": "SCMP_ACT_ALLOW"}

    def test_without_a_profile_podmans_own_default_applies(self, runtime: PodmanRuntime) -> None:
        """Unlike the self-hosted backends, no profile here does not mean unconfined: leaving the
        flag out leaves podman's default profile in place."""
        argv = _argv(runtime, {})

        assert not any(a.startswith("seccomp=") for a in argv)
        assert "no-new-privileges" in argv


class TestLogging:
    def test_no_log_options_before_the_agent_says_where_logs_go(
        self, runtime: PodmanRuntime
    ) -> None:
        """configure_logging runs after open(); until it does, the log root is unknown and naming
        a path would put the container's log somewhere the agent's reader never looks."""
        assert "--log-driver" not in _argv(runtime, {})

    def test_the_log_lands_where_the_agents_reader_looks(
        self, runtime: PodmanRuntime, tmp_path: Path
    ) -> None:
        runtime.configure_logging(tmp_path / "writer", tmp_path / "logs", 5_000_000)

        argv = _argv(runtime, {})

        assert f"path={tmp_path / 'logs' / 'c1.log'}" in argv
        assert "max-size=5000000" in argv
