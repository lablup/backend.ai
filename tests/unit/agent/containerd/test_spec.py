from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import Any

from ai.backend.agent.containerd.spec import (
    CPU_PERIOD_US,
    BindMount,
    SpecInput,
    build_base_spec,
    build_launch_spec,
    merge_env,
)


def _input(
    *,
    cpu_cores: Sequence[int] = (2, 0),
    memory_bytes: int = 1 << 30,
    extra_caps: Sequence[str] = (),
) -> SpecInput:
    return SpecInput(
        cwd="/home/work",
        hostname="main1",
        cpu_cores=cpu_cores,
        memory_bytes=memory_bytes,
        shm_bytes=1 << 26,
        netns_path="/run/netns/bai-t-k1",
        extra_caps=extra_caps,
    )


def _mount(target: str, *, ro: bool = True) -> BindMount:
    return BindMount(source=Path("/host") / target.lstrip("/"), target=target, read_only=ro)


class TestBaseSpec:
    def test_namespaces_in_containerd_order_with_the_kernel_netns(self) -> None:
        spec = build_base_spec(_input())

        assert spec["linux"]["namespaces"] == [
            {"type": "pid"},
            {"type": "ipc"},
            {"type": "uts"},
            {"type": "mount"},
            {"type": "network", "path": "/run/netns/bai-t-k1"},
            {"type": "cgroup"},
        ]

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
        caps = build_base_spec(_input(extra_caps=["CAP_SYS_PTRACE"]))["process"]["capabilities"]

        assert "CAP_IPC_LOCK" in caps["effective"]
        assert "CAP_SYS_NICE" in caps["bounding"]
        assert "CAP_SYS_PTRACE" in caps["permitted"]
        assert "CAP_SYS_ADMIN" not in caps["permitted"]

    def test_raw_sockets_and_privileged_ports_are_allowed_in_the_own_netns(self) -> None:
        caps = build_base_spec(_input())["process"]["capabilities"]

        for kind in ("bounding", "effective", "permitted"):
            assert "CAP_NET_RAW" in caps[kind]
            assert "CAP_NET_BIND_SERVICE" in caps[kind]

    def test_runs_as_root_in_the_work_dir(self) -> None:
        process = build_base_spec(_input())["process"]

        assert process["user"] == {"uid": 0, "gid": 0}
        assert process["cwd"] == "/home/work"
        assert process["terminal"] is False

    def test_shm_size(self) -> None:
        mounts = {m["destination"]: m for m in build_base_spec(_input())["mounts"]}

        assert f"size={1 << 26}" in mounts["/dev/shm"]["options"]
        assert {"/proc", "/dev", "/dev/pts", "/dev/mqueue", "/sys", "/sys/fs/cgroup"} <= set(mounts)

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

    def test_default_mounts_come_before_dev_shm_children(self) -> None:
        order = [m["destination"] for m in build_base_spec(_input())["mounts"]]

        assert order.index("/dev") < order.index("/dev/shm")
        assert order.index("/sys") < order.index("/sys/fs/cgroup")


class TestLaunchSpec:
    base = build_base_spec(_input())

    def _build(self, *, mounts: Sequence[BindMount] = ()) -> dict[str, Any]:
        return build_launch_spec(
            self.base,
            args=["/opt/kernel/entrypoint.sh", "python"],
            env=["A=1"],
            mounts=mounts,
            cgroups_path="/ns/c1",
        )

    def test_args_and_env(self) -> None:
        spec = self._build()

        assert spec["process"]["args"] == ["/opt/kernel/entrypoint.sh", "python"]
        assert spec["process"]["env"] == ["A=1"]

    def test_cgroups_path_is_set(self) -> None:
        assert self._build()["linux"]["cgroupsPath"] == "/ns/c1"

    def test_base_spec_is_not_mutated(self) -> None:
        self._build(mounts=[_mount("/opt/kernel/su-exec")])

        assert self.base["process"]["args"] == []
        assert "cgroupsPath" not in self.base["linux"]
        assert all(m["type"] != "bind" for m in self.base["mounts"])

    def test_mounts_are_binds_ordered_by_depth(self) -> None:
        spec = self._build(
            mounts=[
                _mount("/opt/backend.ai/lib/site/kernel"),
                _mount("/opt/backend.ai"),
                _mount("/home/work", ro=False),
            ]
        )

        binds = [m for m in spec["mounts"] if m["type"] == "bind"]
        assert [m["destination"] for m in binds] == [
            "/opt/backend.ai",
            "/home/work",
            "/opt/backend.ai/lib/site/kernel",
        ]
        assert binds[0]["options"] == ["rbind", "rprivate", "ro"]
        assert binds[1]["options"] == ["rbind", "rprivate", "rw"]
        assert binds[1]["source"] == "/host/home/work"


class TestMergeEnv:
    def test_kernel_env_wins_and_order_is_kept(self) -> None:
        assert merge_env(["PATH=/bin", "LANG=C"], {"LANG": "en", "NEW": "1"}) == [
            "PATH=/bin",
            "LANG=en",
            "NEW=1",
        ]

    def test_value_may_contain_equals(self) -> None:
        assert merge_env(["OPTS=a=b"], {}) == ["OPTS=a=b"]
