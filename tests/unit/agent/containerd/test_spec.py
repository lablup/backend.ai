from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from ai.backend.agent.containerd.profile.base import GeneratedMount, GeneratedMountKind
from ai.backend.agent.containerd.spec import (
    CPU_PERIOD_US,
    SpecInput,
    build_base_spec,
    build_launch_spec,
    merge_env,
    merge_patch,
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
        extra_caps=extra_caps,
    )


def _mount(kind: GeneratedMountKind, target: str, *, ro: bool = True) -> GeneratedMount:
    return GeneratedMount(
        kind=kind, source=Path("/host") / target.lstrip("/"), target=target, read_only=ro
    )


class TestBaseSpec:
    def test_shares_the_host_network(self) -> None:
        spec = build_base_spec(_input())

        types = [ns["type"] for ns in spec["linux"]["namespaces"]]
        assert "network" not in types
        assert {"pid", "ipc", "uts", "mount"} <= set(types)

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

        assert resources == {}

    def test_capabilities_match_the_docker_agent(self) -> None:
        caps = build_base_spec(_input(extra_caps=["CAP_SYS_PTRACE"]))["process"]["capabilities"]

        assert "CAP_IPC_LOCK" in caps["effective"]
        assert "CAP_SYS_NICE" in caps["bounding"]
        assert "CAP_SYS_PTRACE" in caps["permitted"]
        assert "CAP_SYS_ADMIN" not in caps["permitted"]

    def test_runs_as_root_in_the_work_dir(self) -> None:
        process = build_base_spec(_input())["process"]

        assert process["user"] == {"uid": 0, "gid": 0}
        assert process["cwd"] == "/home/work"
        assert process["terminal"] is False

    def test_shm_size(self) -> None:
        mounts = {m["destination"]: m for m in build_base_spec(_input())["mounts"]}

        assert f"size={1 << 26}" in mounts["/dev/shm"]["options"]
        assert {"/proc", "/dev", "/dev/pts", "/dev/mqueue", "/sys", "/sys/fs/cgroup"} <= set(mounts)

    def test_default_mounts_come_before_dev_shm_children(self) -> None:
        order = [m["destination"] for m in build_base_spec(_input())["mounts"]]

        assert order.index("/dev") < order.index("/dev/shm")
        assert order.index("/sys") < order.index("/sys/fs/cgroup")


class TestLaunchSpec:
    base = build_base_spec(_input())

    def _build(
        self,
        *,
        mounts: Sequence[GeneratedMount] = (),
        allowed_mount_kinds: frozenset[GeneratedMountKind] = frozenset(GeneratedMountKind),
        spec_patch: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        return build_launch_spec(
            self.base,
            args=["/opt/kernel/entrypoint.sh", "python"],
            env=["A=1"],
            mounts=mounts,
            allowed_mount_kinds=allowed_mount_kinds,
            spec_patch=spec_patch or {},
        )

    def test_args_and_env(self) -> None:
        spec = self._build()

        assert spec["process"]["args"] == ["/opt/kernel/entrypoint.sh", "python"]
        assert spec["process"]["env"] == ["A=1"]

    def test_base_spec_is_not_mutated(self) -> None:
        self._build(mounts=[_mount(GeneratedMountKind.KRUNNER, "/opt/kernel/su-exec")])

        assert self.base["process"]["args"] == []
        assert all(m["type"] != "bind" for m in self.base["mounts"])

    def test_mounts_are_binds_ordered_by_depth(self) -> None:
        spec = self._build(
            mounts=[
                _mount(GeneratedMountKind.KRUNNER, "/opt/backend.ai/lib/site/kernel"),
                _mount(GeneratedMountKind.KRUNNER, "/opt/backend.ai"),
                _mount(GeneratedMountKind.SCRATCH, "/home/work", ro=False),
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

    def test_disallowed_mount_kinds_are_dropped(self) -> None:
        spec = self._build(
            mounts=[
                _mount(GeneratedMountKind.KRUNNER, "/opt/kernel/su-exec"),
                _mount(GeneratedMountKind.CONFIG_DIR, "/home/config"),
            ],
            allowed_mount_kinds=frozenset({GeneratedMountKind.CONFIG_DIR}),
        )

        binds = [m["destination"] for m in spec["mounts"] if m["type"] == "bind"]
        assert binds == ["/home/config"]

    def test_profile_patch_is_applied_last(self) -> None:
        spec = self._build(
            spec_patch={
                "annotations": {"io.katacontainers.config_path": "/etc/kata.toml"},
                "process": {"cwd": "/srv"},
            }
        )

        assert spec["annotations"] == {"io.katacontainers.config_path": "/etc/kata.toml"}
        assert spec["process"]["cwd"] == "/srv"
        assert spec["process"]["args"] == ["/opt/kernel/entrypoint.sh", "python"]


class TestMergePatch:
    def test_dicts_merge_recursively(self) -> None:
        assert merge_patch({"a": {"b": 1, "c": 2}}, {"a": {"c": 3, "d": 4}}) == {
            "a": {"b": 1, "c": 3, "d": 4}
        }

    def test_lists_and_scalars_replace(self) -> None:
        assert merge_patch({"a": [1, 2], "b": 1}, {"a": [3], "b": 2}) == {"a": [3], "b": 2}

    def test_null_deletes(self) -> None:
        assert merge_patch({"a": 1, "b": 2}, {"a": None}) == {"b": 2}

    def test_inputs_are_not_mutated(self) -> None:
        base = {"a": {"b": 1}}
        patch = {"a": {"c": [1]}}

        merged = merge_patch(base, patch)
        merged["a"]["c"].append(2)

        assert base == {"a": {"b": 1}}
        assert patch == {"a": {"c": [1]}}


class TestMergeEnv:
    def test_kernel_env_wins_and_order_is_kept(self) -> None:
        assert merge_env(["PATH=/bin", "LANG=C"], {"LANG": "en", "NEW": "1"}) == [
            "PATH=/bin",
            "LANG=en",
            "NEW=1",
        ]

    def test_value_may_contain_equals(self) -> None:
        assert merge_env(["OPTS=a=b"], {}) == ["OPTS=a=b"]
