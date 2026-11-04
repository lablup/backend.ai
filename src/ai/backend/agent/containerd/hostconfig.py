"""Translate a compute plugin's Docker container fragment into OCI spec edits."""

from __future__ import annotations

import copy
import os
import stat as stat_mod
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Final, Literal

from ai.backend.agent.containerd.profile.base import TranslatedDevice
from ai.backend.agent.errors.containerd import HostConfigNotTranslatable

_TOP_LEVEL_KEYS: Final = frozenset({"Env", "HostConfig"})
_HOST_CONFIG_KEYS: Final = frozenset({"Devices"})
_DEVICE_KEYS: Final = frozenset({"PathOnHost", "PathInContainer", "CgroupPermissions"})
_ACCESS_ORDER: Final = "rwm"


@dataclass(frozen=True)
class DeviceNode:
    device: TranslatedDevice  # path = PathInContainer; access = CgroupPermissions
    host_path: str
    file_mode: int  # permission bits of the host node (Docker parity)
    uid: int
    gid: int


@dataclass(frozen=True)
class HostConfigTranslation:
    devices: tuple[DeviceNode, ...] = ()
    env: tuple[tuple[str, str], ...] = ()  # in emission order

    @property
    def translated_devices(self) -> tuple[TranslatedDevice, ...]:
        return tuple(node.device for node in self.devices)


def _refuse(plugin: str, key: str, reason: str | None = None) -> HostConfigNotTranslatable:
    suffix = f" ({reason})" if reason else ""
    return HostConfigNotTranslatable(
        f"{plugin}: {key}{suffix}", extra_data={"plugin": plugin, "key": key}
    )


def _check_keys(
    plugin: str, prefix: str, value: Mapping[str, Any], allowed: frozenset[str]
) -> None:
    for key in value:
        if key not in allowed:
            raise _refuse(plugin, f"{prefix}.{key}" if prefix else str(key), "not translatable")


def _mapping(plugin: str, key: str, value: Any) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise _refuse(plugin, key, "not a mapping")
    return value


def _sequence(plugin: str, key: str, value: Any) -> Sequence[Any]:
    if not isinstance(value, list | tuple):
        raise _refuse(plugin, key, "not a list")
    return value


def _validate_access(plugin: str, key: str, access: Any) -> str:
    if (
        not isinstance(access, str)
        or not access
        or len(set(access)) != len(access)
        or not set(access) <= set(_ACCESS_ORDER)
    ):
        raise _refuse(plugin, key, "permissions must be a non-repeating subset of rwm")
    return access


def _device_node(
    plugin: str,
    key: str,
    host_path: str,
    container_path: str,
    access: str,
    stat: Callable[[str], os.stat_result],
) -> DeviceNode:
    # FIXME(containerd-mvp): a missing host node raises; plugins may expect it to be skipped
    try:
        st = stat(host_path)
    except OSError as e:
        raise _refuse(plugin, key, f"cannot stat {host_path}: {e}") from e
    node_type: Literal["c", "b"]
    if stat_mod.S_ISCHR(st.st_mode):
        node_type = "c"
    elif stat_mod.S_ISBLK(st.st_mode):
        node_type = "b"
    else:
        # FIXME(containerd-mvp): Docker expands a device directory, we raise
        raise _refuse(plugin, key, f"{host_path} is not a character or block device")
    major, minor = os.major(st.st_rdev), os.minor(st.st_rdev)
    file_mode, uid, gid = stat_mod.S_IMODE(st.st_mode), st.st_uid, st.st_gid
    return DeviceNode(
        device=TranslatedDevice(container_path, node_type, major, minor, access),
        host_path=host_path,
        file_mode=file_mode,
        uid=uid,
        gid=gid,
    )


def _absolute(plugin: str, key: str, value: Any) -> str:
    if not isinstance(value, str) or not value.startswith("/"):
        raise _refuse(plugin, key, "must be an absolute path")
    return value


def _translate_devices(
    plugin: str, entries: Sequence[Any], stat: Callable[[str], os.stat_result]
) -> list[HostConfigTranslation]:
    out: list[HostConfigTranslation] = []
    for i, entry in enumerate(entries):
        base = f"HostConfig.Devices[{i}]"
        item = _mapping(plugin, base, entry)
        _check_keys(plugin, base, item, _DEVICE_KEYS)
        host_path = _absolute(plugin, f"{base}.PathOnHost", item.get("PathOnHost"))
        container_path = _absolute(
            plugin, f"{base}.PathInContainer", item.get("PathInContainer", host_path)
        )
        access = _validate_access(
            plugin, f"{base}.CgroupPermissions", item.get("CgroupPermissions", "rwm")
        )
        node = _device_node(plugin, base, host_path, container_path, access, stat)
        out.append(HostConfigTranslation(devices=(node,)))
    return out


def _translate_env(
    plugin: str, entries: Sequence[Any], prefix: str = "Env"
) -> list[HostConfigTranslation]:
    pairs: list[tuple[str, str]] = []
    for i, entry in enumerate(entries):
        key = f"{prefix}[{i}]"
        if not isinstance(entry, str):
            raise _refuse(plugin, key, "not a string")
        name, sep, value = entry.partition("=")
        if not sep or not name:
            raise _refuse(plugin, key, "must be NAME=VALUE")
        pairs.append((name, value))
    return [HostConfigTranslation(env=(pair,)) for pair in pairs]


def translate_fragment(
    plugin: str,
    fragment: Mapping[str, Any],
    *,
    stat: Callable[[str], os.stat_result] = os.stat,
) -> HostConfigTranslation:
    """Blocking (stat). Every key but `Env` and `HostConfig.Devices` raises."""
    # Untranslatable keys raise by presence, even when empty.
    top = _mapping(plugin, "<fragment>", fragment)
    _check_keys(plugin, "", top, _TOP_LEVEL_KEYS)
    parts: list[HostConfigTranslation] = []
    if "Env" in top:
        parts.extend(_translate_env(plugin, _sequence(plugin, "Env", top["Env"])))
    host_config = _mapping(plugin, "HostConfig", top.get("HostConfig", {}))
    _check_keys(plugin, "HostConfig", host_config, _HOST_CONFIG_KEYS)
    if "Devices" in host_config:
        entries = _sequence(plugin, "HostConfig.Devices", host_config["Devices"])
        parts.extend(_translate_devices(plugin, entries, stat))
    return merge_translations([(plugin, part) for part in parts])


def _conflict(first: str, second: str, key: str, reason: str) -> HostConfigNotTranslatable:
    return HostConfigNotTranslatable(
        f'"{first}" and "{second}" {reason} ({key})',
        extra_data={"plugins": [first, second], "key": key},
    )


def merge_translations(
    fragments: Sequence[tuple[str, HostConfigTranslation]],
) -> HostConfigTranslation:
    """Union in order; identical duplicates collapse, a conflicting duplicate raises."""
    devices: dict[str, tuple[str, DeviceNode]] = {}
    env: dict[str, tuple[str, str]] = {}
    for plugin, translation in fragments:
        for node in translation.devices:
            path = node.device.path
            if path in devices and devices[path][1] != node:
                raise _conflict(
                    devices[path][0],
                    plugin,
                    f"path {path}",
                    "map the path to different host nodes",
                )
            devices.setdefault(path, (plugin, node))
        for name, value in translation.env:
            if name in env and env[name][1] != value:
                raise _conflict(env[name][0], plugin, f"Env.{name}", "set different values")
            env.setdefault(name, (plugin, value))
    return HostConfigTranslation(
        devices=tuple(node for _, node in devices.values()),
        env=tuple((name, value) for name, (_, value) in env.items()),
    )


def apply_to_spec(
    base_spec: Mapping[str, Any], translation: HostConfigTranslation
) -> dict[str, Any]:
    """Pure; returns a deep copy with the translation applied."""
    spec = copy.deepcopy(dict(base_spec))
    linux = spec["linux"]
    allow_rules = linux["resources"]["devices"]
    seen_rules: set[tuple[str, int, int, str]] = set()
    for node in translation.devices:
        dev = node.device
        linux.setdefault("devices", []).append({
            "path": dev.path,
            "type": dev.type,
            "major": dev.major,
            "minor": dev.minor,
            "fileMode": node.file_mode,
            "uid": node.uid,
            "gid": node.gid,
        })
        rule_key = (dev.type, dev.major, dev.minor, dev.access)
        if rule_key not in seen_rules:
            seen_rules.add(rule_key)
            allow_rules.append({
                "allow": True,
                "type": dev.type,
                "major": dev.major,
                "minor": dev.minor,
                "access": dev.access,
            })
    return spec
