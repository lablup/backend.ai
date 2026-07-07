from ai.backend.agent.containerd.runtime.spec import OCI_VERSION, build_oci_runtime_spec


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

    def test_bind_mounts_appended_after_defaults(self) -> None:
        spec = build_oci_runtime_spec(_oci(), command=["x"], rootfs_path="/r")
        binds = [m for m in spec["mounts"] if m["type"] == "bind"]
        assert binds == [
            {"destination": "/opt/x", "type": "bind", "source": "/host/x",
             "options": ["rbind", "rprivate", "ro"]}
        ]  # fmt: skip
        # default mounts (/proc, /dev, ...) precede binds
        assert spec["mounts"][0]["destination"] == "/proc"

    def test_device_passthrough_adds_device_and_cgroup_rule(self) -> None:
        spec = build_oci_runtime_spec(
            _oci(devices=[{"source": "/dev/kfd", "destination": "/dev/kfd", "permissions": "rw"}]),
            command=["x"],
            rootfs_path="/r",
        )
        assert {"path": "/dev/kfd", "type": "c", "major": -1, "minor": -1} in spec["linux"][
            "devices"
        ]
        rules = spec["linux"]["resources"]["devices"]
        assert rules[0] == {"allow": False, "access": "rwm"}  # deny-all first
        assert {"allow": True, "type": "c", "access": "rw"} in rules

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
