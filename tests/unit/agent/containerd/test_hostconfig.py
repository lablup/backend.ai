from __future__ import annotations

import copy
import os
import stat as stat_mod
from collections.abc import Callable, Mapping
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast

import pytest
import yaml

from ai.backend.agent.containerd.hostconfig import (
    DeviceNode,
    HostConfigTranslation,
    Rlimit,
    apply_to_spec,
    merge_translations,
    translate_fragment,
)
from ai.backend.agent.containerd.profile.base import TranslatedDevice
from ai.backend.agent.errors.containerd import HostConfigNotTranslatable

INFINITY = 2**64 - 1


def _stat_result(
    kind: int, major: int, minor: int, mode: int = 0o666, uid: int = 0, gid: int = 0
) -> os.stat_result:
    return cast(
        os.stat_result,
        SimpleNamespace(
            st_mode=kind | mode, st_rdev=os.makedev(major, minor), st_uid=uid, st_gid=gid
        ),
    )


def _fake_stat(nodes: Mapping[str, os.stat_result]) -> Callable[[str], os.stat_result]:
    def stat(path: str) -> os.stat_result:
        if path not in nodes:
            raise FileNotFoundError(path)
        return nodes[path]

    return stat


def _chr(major: int, minor: int, **kwargs: int) -> os.stat_result:
    return _stat_result(stat_mod.S_IFCHR, major, minor, **kwargs)


STAT = _fake_stat({
    "/dev/fuse": _chr(10, 229),
    "/dev/loop0": _stat_result(stat_mod.S_IFBLK, 7, 0, mode=0o660, uid=0, gid=6),
    "/dev/vfio/devices/vfio0": _chr(237, 0),
    "/dev/dir": _stat_result(stat_mod.S_IFDIR, 0, 0, mode=0o755),
})


def _translate(fragment: Mapping[str, Any], plugin: str = "cuda") -> HostConfigTranslation:
    return translate_fragment(plugin, fragment, stat=STAT)


def _devices(*entries: Mapping[str, Any]) -> dict[str, Any]:
    return {"HostConfig": {"Devices": list(entries)}}


def _node(path: str = "/dev/fuse", major: int = 10, minor: int = 229) -> DeviceNode:
    return DeviceNode(TranslatedDevice(path, "c", major, minor, "rwm"), path, 0o666, 0, 0)


@pytest.fixture
def base_spec() -> dict[str, Any]:
    return {
        "process": {
            "capabilities": {
                "bounding": ["CAP_CHOWN"],
                "effective": ["CAP_CHOWN"],
                "permitted": ["CAP_CHOWN"],
            },
            "rlimits": [
                {"type": "RLIMIT_NOFILE", "soft": 1024, "hard": 1024},
                {"type": "RLIMIT_MEMLOCK", "soft": 64, "hard": 64},
            ],
        },
        "linux": {
            "resources": {"devices": [{"allow": False, "access": "rwm"}]},
            "namespaces": [{"type": "pid"}, {"type": "ipc"}, {"type": "mount"}],
        },
    }


class TestEmptyFragment:
    @pytest.mark.parametrize("fragment", [{}, {"HostConfig": {}}, {"Env": []}])
    def test_empty_fragment_translates_to_nothing(self, fragment: Mapping[str, Any]) -> None:
        assert _translate(fragment) == HostConfigTranslation()


class TestDevices:
    def test_char_device(self) -> None:
        translation = _translate(_devices({"PathOnHost": "/dev/fuse"}))

        assert translation.translated_devices == (
            TranslatedDevice("/dev/fuse", "c", 10, 229, "rwm"),
        )

    def test_block_device(self) -> None:
        translation = _translate(_devices({"PathOnHost": "/dev/loop0"}))

        assert translation.translated_devices == (TranslatedDevice("/dev/loop0", "b", 7, 0, "rwm"),)

    def test_container_path_differs(self) -> None:
        translation = _translate(
            _devices({"PathOnHost": "/dev/fuse", "PathInContainer": "/dev/cc-fuse"})
        )

        (node,) = translation.devices
        assert node.device.path == "/dev/cc-fuse"
        assert node.host_path == "/dev/fuse"
        assert (node.device.major, node.device.minor) == (10, 229)

    def test_permissions_are_kept(self) -> None:
        translation = _translate(_devices({"PathOnHost": "/dev/fuse", "CgroupPermissions": "r"}))

        assert translation.devices[0].device.access == "r"

    def test_file_mode_and_owner_are_copied(self) -> None:
        (node,) = _translate(_devices({"PathOnHost": "/dev/loop0"})).devices

        assert (node.file_mode, node.uid, node.gid) == (0o660, 0, 6)

    @pytest.mark.parametrize("perms", ["rx", "", "rr", "x", 1])
    def test_invalid_permissions_raise(self, perms: Any) -> None:
        fragment = _devices({"PathOnHost": "/dev/fuse", "CgroupPermissions": perms})

        with pytest.raises(HostConfigNotTranslatable, match="CgroupPermissions"):
            _translate(fragment)

    def test_missing_node_raises(self) -> None:
        with pytest.raises(HostConfigNotTranslatable, match="/dev/absent"):
            _translate(_devices({"PathOnHost": "/dev/absent"}))

    def test_directory_raises(self) -> None:
        with pytest.raises(HostConfigNotTranslatable, match="not a character or block"):
            _translate(_devices({"PathOnHost": "/dev/dir"}))

    def test_extra_entry_key_raises(self) -> None:
        with pytest.raises(HostConfigNotTranslatable, match=r"Devices\[0\]\.Extra"):
            _translate(_devices({"PathOnHost": "/dev/fuse", "Extra": 1}))

    @pytest.mark.parametrize(
        "entry",
        [
            {},
            {"PathOnHost": "dev/fuse"},
            {"PathOnHost": "/dev/fuse", "PathInContainer": "rel"},
            {"PathOnHost": 3},
        ],
    )
    def test_bad_paths_raise(self, entry: Mapping[str, Any]) -> None:
        with pytest.raises(HostConfigNotTranslatable, match="Devices"):
            _translate(_devices(entry))

    def test_error_names_plugin_and_key(self) -> None:
        with pytest.raises(HostConfigNotTranslatable) as exc:
            _translate(_devices({"PathOnHost": "/dev/absent"}), plugin="rebellions")

        assert exc.value.extra_data == {"plugin": "rebellions", "key": "HostConfig.Devices[0]"}
        assert exc.value.extra_msg is not None
        assert exc.value.extra_msg.startswith("rebellions: HostConfig.Devices[0]")


class TestC5Fragment:
    def test_vfio_fragment_translates_to_the_library_fixture_device(self) -> None:
        fragment = {
            "HostConfig": {
                "Devices": [
                    {
                        "PathOnHost": "/dev/vfio/devices/vfio0",
                        "PathInContainer": "/dev/vfio/devices/vfio0",
                        "CgroupPermissions": "rwm",
                    }
                ]
            }
        }

        translation = _translate(fragment)

        assert translation.translated_devices == (
            TranslatedDevice("/dev/vfio/devices/vfio0", "c", 237, 0, "rwm"),
        )


class TestCapAdd:
    def test_capability_is_prefixed(self) -> None:
        assert _translate({"HostConfig": {"CapAdd": ["IPC_LOCK"]}}).capabilities == (
            "CAP_IPC_LOCK",
        )

    def test_lower_case_is_normalised(self) -> None:
        translation = _translate({"HostConfig": {"CapAdd": ["cap_sys_nice"]}})

        assert translation.capabilities == ("CAP_SYS_NICE",)

    def test_duplicates_collapse(self) -> None:
        translation = _translate({"HostConfig": {"CapAdd": ["IPC_LOCK", "CAP_IPC_LOCK"]}})

        assert translation.capabilities == ("CAP_IPC_LOCK",)

    @pytest.mark.parametrize("cap", ["ALL", "", "CAP_bad-name", 3])
    def test_invalid_capability_raises(self, cap: Any) -> None:
        with pytest.raises(HostConfigNotTranslatable, match="CapAdd"):
            _translate({"HostConfig": {"CapAdd": [cap]}})


class TestUlimits:
    def test_unlimited_maps_to_infinity(self) -> None:
        fragment = {"HostConfig": {"Ulimits": [{"Name": "memlock", "Soft": -1, "Hard": -1}]}}

        assert _translate(fragment).rlimits == (Rlimit("RLIMIT_MEMLOCK", INFINITY, INFINITY),)

    def test_replaces_the_base_entry_of_the_same_type(self, base_spec: dict[str, Any]) -> None:
        fragment = {"HostConfig": {"Ulimits": [{"Name": "memlock", "Soft": 1, "Hard": 2}]}}

        spec = apply_to_spec(base_spec, _translate(fragment))

        memlock = [r for r in spec["process"]["rlimits"] if r["type"] == "RLIMIT_MEMLOCK"]
        assert memlock == [{"type": "RLIMIT_MEMLOCK", "soft": 1, "hard": 2}]

    def test_new_type_is_appended(self, base_spec: dict[str, Any]) -> None:
        fragment = {"HostConfig": {"Ulimits": [{"Name": "nproc", "Soft": 5, "Hard": 6}]}}

        spec = apply_to_spec(base_spec, _translate(fragment))

        assert spec["process"]["rlimits"][-1] == {"type": "RLIMIT_NPROC", "soft": 5, "hard": 6}
        assert len(spec["process"]["rlimits"]) == len(base_spec["process"]["rlimits"]) + 1

    @pytest.mark.parametrize(
        "entry",
        [
            {"Name": "bogus", "Soft": 1, "Hard": 1},
            {"Name": "nofile", "Hard": 1},
            {"Name": "nofile", "Soft": True, "Hard": 1},
            {"Name": "nofile", "Soft": 2, "Hard": 1},
            {"Name": "nofile", "Soft": -1, "Hard": 1},
            {"Name": "nofile", "Soft": 1, "Hard": 1, "Extra": 1},
        ],
    )
    def test_invalid_ulimit_raises(self, entry: Mapping[str, Any]) -> None:
        with pytest.raises(HostConfigNotTranslatable, match="Ulimits"):
            _translate({"HostConfig": {"Ulimits": [entry]}})


class TestIpcMode:
    def test_host_drops_only_the_ipc_namespace(self, base_spec: dict[str, Any]) -> None:
        translation = _translate({"HostConfig": {"IpcMode": "host"}})

        spec = apply_to_spec(base_spec, translation)

        before = [ns["type"] for ns in base_spec["linux"]["namespaces"]]
        assert [ns["type"] for ns in spec["linux"]["namespaces"]] == [
            t for t in before if t != "ipc"
        ]

    @pytest.mark.parametrize("mode", ["private", "", "container:x", "shareable"])
    def test_other_modes_raise(self, mode: str) -> None:
        with pytest.raises(HostConfigNotTranslatable, match="IpcMode"):
            _translate({"HostConfig": {"IpcMode": mode}})

    def test_ipc_key_raises(self) -> None:
        with pytest.raises(HostConfigNotTranslatable, match=r"HostConfig\.Ipc"):
            _translate({"HostConfig": {"Ipc": "host"}})


class TestEnv:
    def test_order_is_kept(self) -> None:
        assert _translate({"Env": ["B=2", "A=1", "C="]}).env == (("B", "2"), ("A", "1"), ("C", ""))

    def test_value_may_contain_equals(self) -> None:
        assert _translate({"Env": ["A=b=c"]}).env == (("A", "b=c"),)

    @pytest.mark.parametrize("entry", ["FOO", "=x", 3])
    def test_malformed_entry_raises(self, entry: Any) -> None:
        with pytest.raises(HostConfigNotTranslatable, match=r"Env\[0\]"):
            _translate({"Env": [entry]})

    def test_conflicting_duplicate_in_one_fragment_raises(self) -> None:
        with pytest.raises(HostConfigNotTranslatable, match=r"Env\.A"):
            _translate({"Env": ["A=1", "A=2"]})


class TestDeviceRequests:
    @pytest.fixture
    def cdi_dir(self, tmp_path: Path) -> Path:
        spec = {
            "kind": "v.com/gpu",
            "containerEdits": {"env": ["V=1"]},
            "devices": [
                {
                    "name": "0",
                    "containerEdits": {"deviceNodes": [{"path": "/dev/fuse", "permissions": "rw"}]},
                }
            ],
        }
        (tmp_path / "gpu.yaml").write_text(yaml.safe_dump(spec))
        return tmp_path

    def _request(self, **overrides: Any) -> dict[str, Any]:
        request = {"Driver": "cdi", "DeviceIDs": ["v.com/gpu=0"], "Count": 0, "Capabilities": None}
        return {"HostConfig": {"DeviceRequests": [{**request, **overrides}]}}

    def test_cdi_request_resolves_nodes_and_env(self, cdi_dir: Path) -> None:
        translation = translate_fragment(
            "rebellions", self._request(), stat=STAT, cdi_spec_dirs=[cdi_dir]
        )

        assert translation.translated_devices == (
            TranslatedDevice("/dev/fuse", "c", 10, 229, "rw"),
        )
        assert translation.env == (("V", "1"),)

    def test_cdi_node_type_mismatch_raises(self, cdi_dir: Path) -> None:
        spec = {
            "kind": "v.com/blk",
            "devices": [
                {
                    "name": "0",
                    "containerEdits": {"deviceNodes": [{"path": "/dev/fuse", "type": "b"}]},
                }
            ],
        }
        (cdi_dir / "blk.yaml").write_text(yaml.safe_dump(spec))
        fragment = self._request(DeviceIDs=["v.com/blk=0"])

        with pytest.raises(HostConfigNotTranslatable, match="does not match"):
            translate_fragment("p", fragment, stat=STAT, cdi_spec_dirs=[cdi_dir])

    def test_cdi_node_major_mismatch_raises(self, cdi_dir: Path) -> None:
        spec = {
            "kind": "v.com/maj",
            "devices": [
                {
                    "name": "0",
                    "containerEdits": {"deviceNodes": [{"path": "/dev/fuse", "major": 99}]},
                }
            ],
        }
        (cdi_dir / "maj.yaml").write_text(yaml.safe_dump(spec))
        fragment = self._request(DeviceIDs=["v.com/maj=0"])

        with pytest.raises(HostConfigNotTranslatable, match="does not match"):
            translate_fragment("p", fragment, stat=STAT, cdi_spec_dirs=[cdi_dir])

    def test_malformed_cdi_env_is_reported_under_the_request(self, cdi_dir: Path) -> None:
        spec = {"kind": "v.com/env", "devices": [{"name": "0", "containerEdits": {"env": ["BAD"]}}]}
        (cdi_dir / "env.yaml").write_text(yaml.safe_dump(spec))
        fragment = self._request(DeviceIDs=["v.com/env=0"])

        with pytest.raises(HostConfigNotTranslatable, match=r"DeviceRequests\[0\]\.cdi\.env\[0\]"):
            translate_fragment("p", fragment, stat=STAT, cdi_spec_dirs=[cdi_dir])

    def test_missing_spec_fails_closed(self, tmp_path: Path) -> None:
        with pytest.raises(HostConfigNotTranslatable, match="no CDI spec"):
            translate_fragment("p", self._request(), stat=STAT, cdi_spec_dirs=[tmp_path])

    def test_no_cdi_io_without_a_request(self, tmp_path: Path) -> None:
        translation = translate_fragment(
            "p", {"HostConfig": {"Devices": []}}, stat=STAT, cdi_spec_dirs=[tmp_path / "absent"]
        )

        assert translation == HostConfigTranslation()

    @pytest.mark.parametrize("driver", ["nvidia", None])
    def test_non_cdi_driver_raises(self, driver: str | None) -> None:
        with pytest.raises(HostConfigNotTranslatable, match="Driver"):
            _translate(self._request(Driver=driver))

    @pytest.mark.parametrize(
        ("field", "value"),
        [("Count", -1), ("Count", 1), ("Options", {"x": 1}), ("Capabilities", [["gpu"]])],
    )
    def test_non_empty_selectors_raise(self, field: str, value: Any) -> None:
        with pytest.raises(HostConfigNotTranslatable, match=field):
            _translate(self._request(**{field: value}))

    def test_empty_device_ids_raise(self) -> None:
        with pytest.raises(HostConfigNotTranslatable, match="DeviceIDs"):
            _translate(self._request(DeviceIDs=[]))

    def test_unknown_request_key_raises(self) -> None:
        with pytest.raises(HostConfigNotTranslatable, match="Extra"):
            _translate(self._request(Extra=1))


class TestUnknownKeys:
    @pytest.mark.parametrize(
        "host_config",
        [
            {"Sysctls": {"net.core.somaxconn": "1"}},
            {"Sysctls": {}},
            {"Runtime": "nvidia"},
            {"SecurityOpt": ["seccomp=unconfined"]},
            {"GroupAdd": ["video"]},
            {"Mounts": [{"Type": "bind"}]},
            {"Privileged": True},
            {"Privileged": False},
            {"CapDrop": ["ALL"]},
            {"ShmSize": 1},
            {"CpuShares": 1},
            {"Cpus": 1},
            {"Memory": 1},
            {"MemorySwap": 1},
            {"Binds": ["/a:/b"]},
            {"Ipc": "host"},
        ],
    )
    def test_host_config_keys_raise(self, host_config: Mapping[str, Any]) -> None:
        (key,) = host_config

        with pytest.raises(HostConfigNotTranslatable) as exc:
            _translate({"HostConfig": host_config}, plugin="habana")

        assert exc.value.extra_data == {"plugin": "habana", "key": f"HostConfig.{key}"}
        assert exc.value.extra_msg is not None
        assert "habana" in exc.value.extra_msg
        assert f"HostConfig.{key}" in exc.value.extra_msg

    @pytest.mark.parametrize("key", ["Cmd", "Labels", "Devices", "Image"])
    def test_top_level_keys_raise(self, key: str) -> None:
        with pytest.raises(HostConfigNotTranslatable) as exc:
            _translate({key: []}, plugin="ipu")

        assert exc.value.extra_data == {"plugin": "ipu", "key": key}

    def test_known_key_with_an_unknown_one_raises(self) -> None:
        fragment = {"HostConfig": {"Devices": [{"PathOnHost": "/dev/fuse"}], "Sysctls": {}}}

        with pytest.raises(HostConfigNotTranslatable, match="Sysctls"):
            _translate(fragment)

    @pytest.mark.parametrize("fragment", [{"HostConfig": []}, {"Env": "A=1"}, {"HostConfig": None}])
    def test_wrong_value_types_raise(self, fragment: Mapping[str, Any]) -> None:
        with pytest.raises(HostConfigNotTranslatable):
            _translate(fragment)


class TestMerge:
    def test_identical_device_from_two_plugins_deduplicates(self) -> None:
        a = HostConfigTranslation(devices=(_node(),))

        merged = merge_translations([("cuda", a), ("rocm", a)])

        assert merged.devices == (_node(),)

    def test_same_path_different_node_raises_naming_both_plugins(self) -> None:
        a = HostConfigTranslation(devices=(_node(),))
        b = HostConfigTranslation(devices=(_node(minor=1),))

        with pytest.raises(HostConfigNotTranslatable) as exc:
            merge_translations([("cuda", a), ("rocm", b)])

        assert exc.value.extra_data == {"plugins": ["cuda", "rocm"], "key": "path /dev/fuse"}
        assert exc.value.extra_msg is not None
        assert '"cuda" and "rocm"' in exc.value.extra_msg

    def test_same_node_different_access_raises(self) -> None:
        a = HostConfigTranslation(devices=(_node(),))
        read_only = DeviceNode(
            TranslatedDevice("/dev/fuse", "c", 10, 229, "r"), "/dev/fuse", 0o666, 0, 0
        )
        b = HostConfigTranslation(devices=(read_only,))

        with pytest.raises(HostConfigNotTranslatable):
            merge_translations([("cuda", a), ("rocm", b)])

    def test_same_node_at_two_paths_is_allowed(self) -> None:
        merged = merge_translations([
            ("cuda", HostConfigTranslation(devices=(_node("/dev/a"),))),
            ("rocm", HostConfigTranslation(devices=(_node("/dev/b"),))),
        ])

        assert [n.device.path for n in merged.devices] == ["/dev/a", "/dev/b"]

    def test_env_same_value_deduplicates_and_keeps_order(self) -> None:
        a = HostConfigTranslation(env=(("A", "1"), ("B", "2")))
        b = HostConfigTranslation(env=(("C", "3"), ("A", "1")))

        merged = merge_translations([("cuda", a), ("rocm", b)])

        assert merged.env == (("A", "1"), ("B", "2"), ("C", "3"))

    def test_env_different_value_raises(self) -> None:
        a = HostConfigTranslation(env=(("A", "1"),))
        b = HostConfigTranslation(env=(("A", "2"),))

        with pytest.raises(HostConfigNotTranslatable, match=r"Env\.A"):
            merge_translations([("cuda", a), ("rocm", b)])

    def test_rlimit_different_value_raises(self) -> None:
        a = HostConfigTranslation(rlimits=(Rlimit("RLIMIT_NPROC", 1, 2),))
        b = HostConfigTranslation(rlimits=(Rlimit("RLIMIT_NPROC", 1, 3),))

        with pytest.raises(HostConfigNotTranslatable, match="RLIMIT_NPROC"):
            merge_translations([("cuda", a), ("rocm", b)])

    def test_rlimit_same_value_deduplicates(self) -> None:
        a = HostConfigTranslation(rlimits=(Rlimit("RLIMIT_NPROC", 1, 2),))

        assert merge_translations([("cuda", a), ("rocm", a)]).rlimits == a.rlimits

    def test_capabilities_union(self) -> None:
        a = HostConfigTranslation(capabilities=("CAP_A", "CAP_B"))
        b = HostConfigTranslation(capabilities=("CAP_B", "CAP_C"))

        merged = merge_translations([("cuda", a), ("rocm", b)])

        assert merged.capabilities == ("CAP_A", "CAP_B", "CAP_C")

    def test_host_ipc_is_ored(self) -> None:
        merged = merge_translations([
            ("cuda", HostConfigTranslation()),
            ("rocm", HostConfigTranslation(host_ipc=True)),
        ])

        assert merged.host_ipc is True

    def test_same_plugin_twice_merges(self) -> None:
        a = HostConfigTranslation(devices=(_node(),), env=(("A", "1"),))
        b = HostConfigTranslation(devices=(_node("/dev/b"),), env=(("A", "1"),))

        merged = merge_translations([("cuda", a), ("cuda", b)])

        assert len(merged.devices) == 2
        assert merged.env == (("A", "1"),)

    def test_no_fragments_merge_to_nothing(self) -> None:
        assert merge_translations([]) == HostConfigTranslation()


class TestApplyToSpec:
    def test_allow_rules_follow_the_deny_all(self, base_spec: dict[str, Any]) -> None:
        translation = HostConfigTranslation(devices=(_node(),))

        spec = apply_to_spec(base_spec, translation)

        assert spec["linux"]["resources"]["devices"] == [
            {"allow": False, "access": "rwm"},
            {"allow": True, "type": "c", "major": 10, "minor": 229, "access": "rwm"},
        ]
        assert spec["linux"]["devices"] == [
            {
                "path": "/dev/fuse",
                "type": "c",
                "major": 10,
                "minor": 229,
                "fileMode": 0o666,
                "uid": 0,
                "gid": 0,
            }
        ]

    def test_two_paths_to_one_node_share_an_allow_rule(self, base_spec: dict[str, Any]) -> None:
        translation = HostConfigTranslation(devices=(_node("/dev/a"), _node("/dev/b")))

        spec = apply_to_spec(base_spec, translation)

        assert len(spec["linux"]["resources"]["devices"]) == 2
        assert len(spec["linux"]["devices"]) == 2

    def test_capabilities_join_all_three_sets(self, base_spec: dict[str, Any]) -> None:
        translation = HostConfigTranslation(capabilities=("CAP_SYS_ADMIN", "CAP_CHOWN"))

        spec = apply_to_spec(base_spec, translation)

        for name in ("bounding", "effective", "permitted"):
            caps = spec["process"]["capabilities"][name]
            assert caps.count("CAP_SYS_ADMIN") == 1
            assert caps.count("CAP_CHOWN") == 1

    def test_base_spec_is_not_mutated(self, base_spec: dict[str, Any]) -> None:
        before = copy.deepcopy(base_spec)
        translation = HostConfigTranslation(
            devices=(_node(),),
            capabilities=("CAP_SYS_ADMIN",),
            rlimits=(Rlimit("RLIMIT_MEMLOCK", 1, 1),),
            host_ipc=True,
        )

        apply_to_spec(base_spec, translation)

        assert base_spec == before

    def test_empty_translation_keeps_the_spec(self, base_spec: dict[str, Any]) -> None:
        assert apply_to_spec(base_spec, HostConfigTranslation()) == base_spec
