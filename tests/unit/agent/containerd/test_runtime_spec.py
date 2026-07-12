from pathlib import Path

import yaml

from ai.backend.agent.containerd.runtime.spec import (
    _DEFAULT_CAPS,
    OCI_VERSION,
    build_oci_runtime_spec,
    container_cgroup_fs_path,
)


def _oci(**over: object) -> dict[str, object]:
    base: dict[str, object] = {
        "env": {"A": "1"},
        "labels": {"ai.backend.kernel-id": "kern-1"},
        "mounts": [{"source": "/host/x", "destination": "/opt/x", "readonly": True}],
    }
    base.update(over)
    return base


class TestBuildOciRuntimeSpec:
    def test_core_process_and_root(self) -> None:
        spec = build_oci_runtime_spec(
            _oci(), command=["/entry", "run"], rootfs_path="/run/rootfs", cwd="/home/work"
        )
        assert spec["ociVersion"] == OCI_VERSION
        assert spec["process"]["args"] == ["/entry", "run"]
        assert "A=1" in spec["process"]["env"]
        assert spec["process"]["cwd"] == "/home/work"
        assert spec["root"] == {"path": "/run/rootfs", "readonly": False}

    def test_default_capabilities_when_no_extra(self) -> None:
        caps = build_oci_runtime_spec(_oci(), command=["x"], rootfs_path="/r")["process"][
            "capabilities"
        ]
        assert caps["bounding"] == _DEFAULT_CAPS
        assert caps["effective"] == _DEFAULT_CAPS and caps["permitted"] == _DEFAULT_CAPS

    def test_extra_caps_appended_without_duplicates(self) -> None:
        # the jail sandbox requests CAP_SYS_PTRACE; a cap already in the default set is not doubled
        spec = build_oci_runtime_spec(
            _oci(extra_caps=["CAP_SYS_PTRACE", "CAP_IPC_LOCK"]), command=["x"], rootfs_path="/r"
        )
        caps = spec["process"]["capabilities"]["bounding"]
        assert caps[: len(_DEFAULT_CAPS)] == _DEFAULT_CAPS
        assert caps[len(_DEFAULT_CAPS) :] == [
            "CAP_SYS_PTRACE"
        ]  # IPC_LOCK already present, not added
        assert "CAP_SYS_PTRACE" in spec["process"]["capabilities"]["effective"]

    def test_bind_mounts_appended_after_defaults(self) -> None:
        spec = build_oci_runtime_spec(_oci(), command=["x"], rootfs_path="/r")
        binds = [m for m in spec["mounts"] if m["type"] == "bind"]
        assert binds == [
            {"destination": "/opt/x", "type": "bind", "source": "/host/x",
             "options": ["rbind", "rprivate", "ro"]}
        ]  # fmt: skip
        # default mounts (/proc, /dev, ...) precede binds
        assert spec["mounts"][0]["destination"] == "/proc"

    def test_device_passthrough_carries_the_real_major_minor(self) -> None:
        # /dev/null is char 1:3 everywhere. runc mknod()s the node inside the container from these
        # numbers, so passing -1 (as we used to) cannot produce a working device.
        spec = build_oci_runtime_spec(
            _oci(
                devices=[{"source": "/dev/null", "destination": "/dev/null", "permissions": "rw"}]
            ),
            command=["x"],
            rootfs_path="/r",
        )
        (device,) = spec["linux"]["devices"]
        assert device["path"] == "/dev/null"
        assert device["type"] == "c"
        assert (device["major"], device["minor"]) == (1, 3)

    def test_cgroup_rule_is_scoped_to_the_device_not_a_wildcard(self) -> None:
        # An OCI device rule with no major/minor is a WILDCARD: allowing one NPU would have
        # allowed every character device on the host — weaker isolation than Docker grants.
        spec = build_oci_runtime_spec(
            _oci(
                devices=[{"source": "/dev/null", "destination": "/dev/null", "permissions": "rw"}]
            ),
            command=["x"],
            rootfs_path="/r",
        )
        rules = spec["linux"]["resources"]["devices"]
        assert rules[0] == {"allow": False, "access": "rwm"}  # deny-all first
        allow_rules = [r for r in rules if r["allow"]]
        assert allow_rules == [{"allow": True, "type": "c", "major": 1, "minor": 3, "access": "rw"}]
        for rule in allow_rules:
            assert rule.get("major") is not None and rule.get("minor") is not None

    def test_a_remapped_device_stats_the_host_source(self) -> None:
        # Plugins rename nodes (/dev/rngd/npu3 -> npu0); the numbers must come from the SOURCE.
        spec = build_oci_runtime_spec(
            _oci(devices=[{"source": "/dev/null", "destination": "/dev/npu0"}]),
            command=["x"],
            rootfs_path="/r",
        )
        (device,) = spec["linux"]["devices"]
        assert device["path"] == "/dev/npu0"
        assert (device["major"], device["minor"]) == (1, 3)

    def test_a_missing_device_is_skipped(self) -> None:
        spec = build_oci_runtime_spec(
            _oci(devices=[{"source": "/dev/does-not-exist", "destination": "/dev/x"}]),
            command=["x"],
            rootfs_path="/r",
        )
        assert spec["linux"]["devices"] == []
        assert [r for r in spec["linux"]["resources"]["devices"] if r["allow"]] == []

    def test_network_ns_pinned_when_path_given(self) -> None:
        spec = build_oci_runtime_spec(
            _oci(), command=["x"], rootfs_path="/r", network_ns_path="/proc/42/ns/net"
        )
        net = [ns for ns in spec["linux"]["namespaces"] if ns["type"] == "network"][0]
        assert net["path"] == "/proc/42/ns/net"

    def test_network_ns_fresh_when_no_path(self) -> None:
        spec = build_oci_runtime_spec(_oci(), command=["x"], rootfs_path="/r")
        net = [ns for ns in spec["linux"]["namespaces"] if ns["type"] == "network"][0]
        assert "path" not in net

    def test_cgroups_path_uses_kernel_id(self) -> None:
        spec = build_oci_runtime_spec(_oci(), command=["x"], rootfs_path="/r")
        assert spec["linux"]["cgroupsPath"] == "/backend-ai/kern-1"

    def test_cgroup_fs_path_matches_spec_cgroups_path(self) -> None:
        # The stats reader (agent.get_cgroup_path -> container_cgroup_fs_path) must resolve to the
        # exact cgroup the spec tells the runtime to create; otherwise utilization reads the wrong
        # (or a nonexistent) cgroup. This locks the two derivations together.
        spec = build_oci_runtime_spec(_oci(), command=["x"], rootfs_path="/r")
        assert container_cgroup_fs_path("kern-1") == Path("/sys/fs/cgroup") / str(
            spec["linux"]["cgroupsPath"]
        ).lstrip("/")

    def test_cpu_and_memory_limits_emitted(self) -> None:
        spec = build_oci_runtime_spec(
            _oci(
                cpuset_cpus="0,2,4",
                cpuset_mems="0",
                memory_limit=2147483648,
                memory_swap=2147483648,
            ),
            command=["x"],
            rootfs_path="/r",
        )
        res = spec["linux"]["resources"]
        assert res["cpu"] == {"cpus": "0,2,4", "mems": "0"}
        assert res["memory"] == {"limit": 2147483648, "swap": 2147483648}

    def test_no_resource_keys_when_unlimited(self) -> None:
        res = build_oci_runtime_spec(_oci(), command=["x"], rootfs_path="/r")["linux"]["resources"]
        assert "cpu" not in res  # no cpuset -> omit (unbounded), don't emit empty dicts
        assert "memory" not in res


class TestFidelity:
    def test_extra_caps_for_hugepages_and_gpudirect(self) -> None:
        spec = build_oci_runtime_spec(_oci(), command=["x"], rootfs_path="/r")
        caps = spec["process"]["capabilities"]["bounding"]
        assert "CAP_IPC_LOCK" in caps and "CAP_SYS_NICE" in caps

    def test_rlimits_present(self) -> None:
        spec = build_oci_runtime_spec(_oci(), command=["x"], rootfs_path="/r")
        types = {r["type"] for r in spec["process"]["rlimits"]}
        assert {"RLIMIT_NOFILE", "RLIMIT_MEMLOCK"} <= types

    def test_shm_size_defaults(self) -> None:
        spec = build_oci_runtime_spec(_oci(), command=["x"], rootfs_path="/r")
        shm = [m for m in spec["mounts"] if m["destination"] == "/dev/shm"][0]
        assert any(o.startswith("size=") for o in shm["options"])

    def test_shm_size_from_resource_opts(self) -> None:
        spec = build_oci_runtime_spec(_oci(shmem=134217728), command=["x"], rootfs_path="/r")
        shm = [m for m in spec["mounts"] if m["destination"] == "/dev/shm"][0]
        assert "size=134217728" in shm["options"]


class TestNvidiaGpuLegacyHook:
    # cdi_dirs points at nothing so CDI never resolves -> the nvidia-container-toolkit prestart
    # hook fallback is exercised deterministically (independent of the host's /etc/cdi).
    _NO_CDI = ("/nonexistent-cdi",)

    def test_hook_and_env_emitted_when_gpus_present(self) -> None:
        spec = build_oci_runtime_spec(
            _oci(gpus=["0", "3"]), command=["x"], rootfs_path="/r", cdi_dirs=self._NO_CDI
        )
        hook = spec["hooks"]["prestart"][0]
        assert hook["path"].endswith("nvidia-container-runtime-hook")
        assert "NVIDIA_VISIBLE_DEVICES=0,3" in spec["process"]["env"]
        assert any(e.startswith("NVIDIA_DRIVER_CAPABILITIES=") for e in spec["process"]["env"])

    def test_no_hooks_without_gpus(self) -> None:
        spec = build_oci_runtime_spec(_oci(), command=["x"], rootfs_path="/r")
        assert "hooks" not in spec

    def test_allocation_overrides_preexisting_visible_devices(self) -> None:
        # The allocation is authoritative: an image that bakes in NVIDIA_VISIBLE_DEVICES
        # (commonly "all") must not leak GPUs the session was not allocated.
        spec = build_oci_runtime_spec(
            _oci(gpus=["0"], env={"NVIDIA_VISIBLE_DEVICES": "all"}),
            command=["x"],
            rootfs_path="/r",
            cdi_dirs=self._NO_CDI,
        )
        vis = [e for e in spec["process"]["env"] if e.startswith("NVIDIA_VISIBLE_DEVICES=")]
        assert vis == ["NVIDIA_VISIBLE_DEVICES=0"]  # allocated GPUs win, image "all" dropped


class TestNvidiaGpuCdi:
    def test_cdi_injection_used_over_legacy_hook(self, tmp_path: Path) -> None:
        (tmp_path / "nvidia.yaml").write_text(
            yaml.safe_dump({
                "cdiVersion": "0.5.0",
                "kind": "nvidia.com/gpu",
                "containerEdits": {
                    "deviceNodes": [{"path": "/dev/nvidiactl", "major": 195, "minor": 255}],
                    "hooks": [
                        {
                            "hookName": "createContainer",
                            "path": "/usr/bin/nvidia-cdi-hook",
                            "args": ["nvidia-cdi-hook", "update-ldcache"],
                        }
                    ],
                },
                "devices": [
                    {
                        "name": "0",
                        "containerEdits": {
                            "deviceNodes": [{"path": "/dev/nvidia0", "major": 195, "minor": 0}]
                        },
                    }
                ],
            })
        )
        spec = build_oci_runtime_spec(
            _oci(gpus=["0"]), command=["x"], rootfs_path="/r", cdi_dirs=[str(tmp_path)]
        )
        # CDI path: device nodes injected + nvidia-cdi-hook, and NOT the legacy prestart hook.
        assert any(d["path"] == "/dev/nvidia0" for d in spec["linux"]["devices"])
        assert spec["hooks"]["createContainer"][0]["path"].endswith("nvidia-cdi-hook")
        assert "prestart" not in spec.get("hooks", {})


class TestAcceleratorHostConfigReachesTheSpec:
    """The NPU/IPU/ROCm plugins emit more than devices; dropping the rest starts a container that
    then misbehaves inside the vendor runtime, which is far harder to diagnose than a refusal."""

    def test_sysctls_are_emitted(self) -> None:
        spec = build_oci_runtime_spec(
            _oci(sysctls={"net.ipv6.conf.all.disable_ipv6": "0"}),
            command=["x"],
            rootfs_path="/r",
        )
        assert spec["linux"]["sysctl"] == {"net.ipv6.conf.all.disable_ipv6": "0"}

    def test_host_ipc_drops_the_ipc_namespace(self) -> None:
        # In the OCI spec, sharing the host's IPC namespace means OMITTING the ipc entry.
        types = {
            ns["type"]
            for ns in build_oci_runtime_spec(_oci(ipc_host=True), command=["x"], rootfs_path="/r")[
                "linux"
            ]["namespaces"]
        }
        assert "ipc" not in types

    def test_ipc_namespace_present_by_default(self) -> None:
        types = {
            ns["type"]
            for ns in build_oci_runtime_spec(_oci(), command=["x"], rootfs_path="/r")["linux"][
                "namespaces"
            ]
        }
        assert "ipc" in types

    def test_additional_gids_reach_the_process_user(self) -> None:
        # ROCm's video/render: without them the container cannot open the device it was given.
        spec = build_oci_runtime_spec(
            _oci(additional_gids=[44, 109]), command=["x"], rootfs_path="/r"
        )
        assert spec["process"]["user"]["additionalGids"] == [44, 109]

    def test_plugin_rlimits_override_the_default_of_the_same_type(self) -> None:
        spec = build_oci_runtime_spec(
            _oci(rlimits=[{"type": "RLIMIT_MEMLOCK", "soft": 100, "hard": 200}]),
            command=["x"],
            rootfs_path="/r",
        )
        memlock = [r for r in spec["process"]["rlimits"] if r["type"] == "RLIMIT_MEMLOCK"]
        assert memlock == [{"type": "RLIMIT_MEMLOCK", "soft": 100, "hard": 200}]
        # the untouched default survives
        assert any(r["type"] == "RLIMIT_NOFILE" for r in spec["process"]["rlimits"])


class TestIdentity:
    def test_hostname_is_taken_from_the_spec(self) -> None:
        # Docker sets Hostname=cluster_hostname (main1/sub1/...). Leaving runc's default made
        # `hostname` inside the container report a container-id prefix — which is exactly what
        # MPI/torchrun read to work out which rank they are.
        spec = build_oci_runtime_spec(_oci(), command=["x"], rootfs_path="/r", hostname="main1")
        assert spec["hostname"] == "main1"

    def test_working_dir_is_taken_from_the_spec(self) -> None:
        spec = build_oci_runtime_spec(_oci(), command=["x"], rootfs_path="/r", cwd="/home/work")
        assert spec["process"]["cwd"] == "/home/work"


class TestAppArmor:
    """dockerd confines every container with its docker-default profile. runc applies nothing
    unless the spec names one, so without this a containerd kernel runs unconfined — strictly
    weaker isolation than the same kernel gets under Docker, and nothing says so.
    """

    def test_the_profile_reaches_the_process(self) -> None:
        spec = build_oci_runtime_spec(
            _oci(apparmor_profile="backendai-default"), command=["x"], rootfs_path="/r"
        )
        assert spec["process"]["apparmorProfile"] == "backendai-default"

    def test_no_profile_means_no_key(self) -> None:
        # A host without AppArmor must not get a spec naming a profile runc cannot find.
        spec = build_oci_runtime_spec(_oci(), command=["x"], rootfs_path="/r")
        assert "apparmorProfile" not in spec["process"]
