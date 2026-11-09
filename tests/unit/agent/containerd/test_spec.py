from __future__ import annotations

from collections.abc import Sequence
from dataclasses import replace
from typing import Any
from unittest.mock import patch

import pytest

from ai.backend.agent.containerd.spec import (
    CPU_PERIOD_US,
    DEFAULT_SHM_BYTES,
    SpecInput,
    build_base_spec,
    build_launch_spec,
    merge_env,
)


def _input(
    *,
    cpu_cores: Sequence[int] = (2, 0),
    memory_bytes: int = 1 << 30,
    shm_bytes: int = 1 << 26,
    extra_caps: Sequence[str] = (),
) -> SpecInput:
    return SpecInput(
        hostname="main1",
        cpu_cores=cpu_cores,
        memory_bytes=memory_bytes,
        shm_bytes=shm_bytes,
        extra_caps=extra_caps,
    )


class TestBaseSpec:
    def test_namespaces_in_containerd_order_with_a_new_netns(self) -> None:
        spec = build_base_spec(_input())

        assert spec["linux"]["namespaces"] == [
            {"type": "pid"},
            {"type": "ipc"},
            {"type": "uts"},
            {"type": "mount"},
            {"type": "network"},
            {"type": "cgroup"},
        ]
        network = next(n for n in spec["linux"]["namespaces"] if n["type"] == "network")
        assert "path" not in network

    def test_netns_path_is_joined(self) -> None:
        spec = build_base_spec(replace(_input(), netns_path="/run/netns/bai0-x"))

        assert {"type": "network", "path": "/run/netns/bai0-x"} in spec["linux"]["namespaces"]

    def test_cpu_and_memory_limits(self) -> None:
        resources = build_base_spec(_input())["linux"]["resources"]

        assert resources["cpu"] == {
            "quota": 2 * CPU_PERIOD_US,
            "period": CPU_PERIOD_US,
            "cpus": "0,2",
        }
        assert resources["memory"] == {"limit": 1 << 30, "swap": 1 << 30}

    def test_no_limits_without_allocation(self) -> None:
        resources = build_base_spec(_input(cpu_cores=[], memory_bytes=0))["linux"]["resources"]

        assert resources == {"devices": [{"allow": False, "access": "rwm"}]}

    def test_capabilities_match_the_docker_agent(self) -> None:
        caps = build_base_spec(_input())["process"]["capabilities"]

        expected = {
            "CAP_CHOWN",
            "CAP_DAC_OVERRIDE",
            "CAP_FSETID",
            "CAP_FOWNER",
            "CAP_MKNOD",
            "CAP_NET_RAW",
            "CAP_SETGID",
            "CAP_SETUID",
            "CAP_SETFCAP",
            "CAP_SETPCAP",
            "CAP_NET_BIND_SERVICE",
            "CAP_SYS_CHROOT",
            "CAP_KILL",
            "CAP_AUDIT_WRITE",
            "CAP_IPC_LOCK",
            "CAP_SYS_NICE",
        }
        for kind in ("bounding", "effective", "permitted"):
            assert set(caps[kind]) == expected
            assert len(caps[kind]) == len(expected)

    def test_extra_caps_get_the_prefix_and_no_duplicates(self) -> None:
        spec = build_base_spec(_input(extra_caps=["SYS_PTRACE", "CAP_IPC_LOCK", "CAP_SYS_PTRACE"]))
        caps = spec["process"]["capabilities"]["permitted"]

        assert caps.count("CAP_SYS_PTRACE") == 1
        assert caps.count("CAP_IPC_LOCK") == 1
        assert "SYS_PTRACE" not in caps

    def test_raw_sockets_and_privileged_ports_are_allowed_in_the_own_netns(self) -> None:
        caps = build_base_spec(_input())["process"]["capabilities"]

        for kind in ("bounding", "effective", "permitted"):
            assert "CAP_NET_RAW" in caps[kind]
            assert "CAP_NET_BIND_SERVICE" in caps[kind]

    def test_runs_as_root(self) -> None:
        process = build_base_spec(_input())["process"]

        assert process["user"] == {"uid": 0, "gid": 0}
        assert process["terminal"] is False

    @pytest.mark.parametrize(
        ("shm_bytes", "expected"), [(1 << 26, 1 << 26), (0, DEFAULT_SHM_BYTES)]
    )
    def test_shm_size(self, shm_bytes: int, expected: int) -> None:
        mounts = {
            m["destination"]: m for m in build_base_spec(_input(shm_bytes=shm_bytes))["mounts"]
        }

        assert f"size={expected}" in mounts["/dev/shm"]["options"]

    def test_rlimits_map_unlimited_to_rlim_infinity(self) -> None:
        def safe_ulimit(name: str, soft: int, hard: int) -> dict[str, Any]:
            return {"Name": name, "Soft": soft, "Hard": hard}

        with patch("ai.backend.agent.containerd.spec.get_safe_ulimit", side_effect=safe_ulimit):
            rlimits = build_base_spec(_input())["process"]["rlimits"]

        assert rlimits == [
            {"type": "RLIMIT_NOFILE", "soft": 1048576, "hard": 1048576},
            {"type": "RLIMIT_MEMLOCK", "soft": 2**64 - 1, "hard": 2**64 - 1},
        ]

    def test_masked_and_readonly_paths_match_containerd_defaults(self) -> None:
        linux = build_base_spec(_input())["linux"]

        assert linux["maskedPaths"] == [
            "/proc/acpi",
            "/proc/asound",
            "/proc/kcore",
            "/proc/keys",
            "/proc/latency_stats",
            "/proc/timer_list",
            "/proc/timer_stats",
            "/proc/sched_debug",
            "/sys/firmware",
            "/sys/devices/virtual/powercap",
            "/proc/scsi",
        ]
        assert linux["readonlyPaths"] == [
            "/proc/bus",
            "/proc/fs",
            "/proc/irq",
            "/proc/sys",
            "/proc/sysrq-trigger",
        ]

    def test_mounts_come_after_their_parents(self) -> None:
        order = [m["destination"] for m in build_base_spec(_input())["mounts"]]

        assert order == [
            "/proc",
            "/dev",
            "/dev/pts",
            "/dev/shm",
            "/dev/mqueue",
            "/sys",
            "/sys/fs/cgroup",
        ]


class TestLaunchSpec:
    @pytest.fixture
    def base(self) -> dict[str, Any]:
        return build_base_spec(_input())

    def _build(self, base: dict[str, Any]) -> dict[str, Any]:
        return build_launch_spec(
            base,
            args=["/bin/sh", "-c", "sleep infinity"],
            env=["A=1"],
            cwd="/srv",
            cgroups_path="/ns/c1",
        )

    def test_args_env_and_working_dir(self, base: dict[str, Any]) -> None:
        spec = self._build(base)

        assert spec["process"]["args"] == ["/bin/sh", "-c", "sleep infinity"]
        assert spec["process"]["env"] == ["A=1"]
        assert spec["process"]["cwd"] == "/srv"

    def test_cgroups_path_is_set(self, base: dict[str, Any]) -> None:
        assert self._build(base)["linux"]["cgroupsPath"] == "/ns/c1"

    def test_base_spec_is_not_mutated(self, base: dict[str, Any]) -> None:
        self._build(base)

        assert base["process"]["args"] == []
        assert base["process"]["cwd"] == "/"
        assert "cgroupsPath" not in base["linux"]


class TestMergeEnv:
    def test_kernel_env_wins_and_order_is_kept(self) -> None:
        assert merge_env(["PATH=/bin", "LANG=C"], {"LANG": "en", "NEW": "1"}) == [
            "PATH=/bin",
            "LANG=en",
            "NEW=1",
        ]

    def test_value_may_contain_equals(self) -> None:
        assert merge_env(["OPTS=a=b"], {}) == ["OPTS=a=b"]

    def test_image_entry_without_equals_sets_nothing(self) -> None:
        assert merge_env(["NOVALUE", "A=1"], {}) == ["A=1"]
