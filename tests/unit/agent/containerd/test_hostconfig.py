from __future__ import annotations

import os
import stat as stat_mod
from collections.abc import Callable
from types import SimpleNamespace
from typing import Any, cast

import pytest

from ai.backend.agent.containerd.hostconfig import (
    DeviceNode,
    HostConfigTranslation,
    apply_to_spec,
    merge_translations,
    translate_fragment,
)
from ai.backend.agent.containerd.spec import SpecInput, build_base_spec
from ai.backend.agent.errors.containerd import HostConfigNotTranslatable


def _stat(mode: int = stat_mod.S_IFCHR | 0o660) -> Callable[[str], os.stat_result]:
    def stat(path: str) -> os.stat_result:
        if path == "/dev/missing":
            raise FileNotFoundError(path)
        return cast(
            os.stat_result,
            SimpleNamespace(st_mode=mode, st_rdev=os.makedev(195, 3), st_uid=7, st_gid=44),
        )

    return stat


def _device(**entry: str) -> dict[str, Any]:
    return {"HostConfig": {"Devices": [{"PathOnHost": "/dev/accel0", **entry}]}}


class TestTranslateFragment:
    def test_device_and_env_are_translated(self) -> None:
        fragment = {**_device(PathInContainer="/dev/a", CgroupPermissions="rw"), "Env": ["K=a=b"]}

        result = translate_fragment("acc", fragment, stat=_stat())

        assert result == HostConfigTranslation(
            devices=(DeviceNode("/dev/a", "c", 195, 3, "rw", 0o660, 7, 44),),
            env=(("K", "a=b"),),
        )

    def test_block_device_with_defaults(self) -> None:
        node = translate_fragment("acc", _device(), stat=_stat(stat_mod.S_IFBLK | 0o600)).devices[0]

        assert (node.type, node.path, node.access) == ("b", "/dev/accel0", "rwm")

    def test_empty_fragment_translates_to_nothing(self) -> None:
        assert translate_fragment("acc", {}) == HostConfigTranslation()

    @pytest.mark.parametrize(
        "fragment",
        [
            {"HostConfig": {"Privileged": False}},
            {"Binds": []},
            _device(Extra="x"),
            _device(CgroupPermissions="rx"),
            {"HostConfig": {"Devices": [{"PathOnHost": "dev/accel0"}]}},
            {"HostConfig": {"Devices": [{"PathOnHost": "/dev/missing"}]}},
            {"HostConfig": {"Devices": [{"PathInContainer": "/dev/a"}]}},
            _device(PathInContainer="dev/a"),
            _device(PathInContainer="/opt/a"),
            _device(PathInContainer="/dev/../etc/a"),
            {"HostConfig": []},
            {"HostConfig": {"Devices": "/dev/accel0"}},
            {"HostConfig": {"Devices": ["/dev/accel0"]}},
            {"Env": "K=V"},
            {"Env": ["NOVALUE"]},
        ],
    )
    def test_invalid_or_untranslatable_fragment_raises(self, fragment: dict[str, Any]) -> None:
        with pytest.raises(HostConfigNotTranslatable):
            translate_fragment("acc", fragment, stat=_stat())

    def test_non_device_node_raises(self) -> None:
        with pytest.raises(HostConfigNotTranslatable, match="not a character or block"):
            translate_fragment("acc", _device(), stat=_stat(stat_mod.S_IFREG | 0o644))


class TestMergeTranslations:
    NODE = DeviceNode("/dev/a", "c", 1, 2, "rw", 0o660, 0, 0)

    def test_identical_duplicates_collapse(self) -> None:
        one = HostConfigTranslation(devices=(self.NODE,), env=(("K", "v"),))

        assert merge_translations([("a", one), ("b", one)]) == one

    def test_conflicting_device_raises(self) -> None:
        other = DeviceNode("/dev/a", "c", 1, 3, "rw", 0o660, 0, 0)

        with pytest.raises(HostConfigNotTranslatable, match="/dev/a"):
            merge_translations([
                ("a", HostConfigTranslation(devices=(self.NODE,))),
                ("b", HostConfigTranslation(devices=(other,))),
            ])

    def test_equivalent_paths_conflict(self) -> None:
        other = DeviceNode("/dev//a/", "c", 1, 3, "rw", 0o660, 0, 0)

        with pytest.raises(HostConfigNotTranslatable):
            merge_translations([
                ("a", HostConfigTranslation(devices=(self.NODE,))),
                ("b", HostConfigTranslation(devices=(other,))),
            ])

    def test_conflicting_env_raises(self) -> None:
        with pytest.raises(HostConfigNotTranslatable, match=r"Env\.K"):
            merge_translations([
                ("a", HostConfigTranslation(env=(("K", "1"),))),
                ("b", HostConfigTranslation(env=(("K", "2"),))),
            ])


class TestApplyToSpec:
    def test_device_node_and_allow_rule_are_added_once_to_a_copy(self) -> None:
        base = build_base_spec(SpecInput("h", [0], 0, 0))
        node = DeviceNode("/dev/a", "c", 195, 3, "rw", 0o660, 7, 44)
        twin = DeviceNode("/dev/b", "c", 195, 3, "rw", 0o660, 7, 44)

        spec = apply_to_spec(base, HostConfigTranslation(devices=(node, twin)))

        assert [d["path"] for d in spec["linux"]["devices"]] == ["/dev/a", "/dev/b"]
        assert spec["linux"]["devices"][0]["fileMode"] == 0o660
        assert spec["linux"]["resources"]["devices"][1:] == [
            {"allow": True, "type": "c", "major": 195, "minor": 3, "access": "rw"}
        ]
        assert "devices" not in base["linux"]
