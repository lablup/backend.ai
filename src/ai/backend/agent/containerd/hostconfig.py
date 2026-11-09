"""Translate a compute plugin's Docker container fragment into OCI spec edits."""

from __future__ import annotations

import copy
import os
import posixpath
import stat as stat_mod
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Final

from ai.backend.agent.errors.containerd import HostConfigNotTranslatable

_DEVICE_KEYS: Final = frozenset({"PathOnHost", "PathInContainer", "CgroupPermissions"})


@dataclass(frozen=True)
class DeviceNode:
    path: str  # in the container
    type: str  # "c" or "b"
    major: int
    minor: int
    access: str
    file_mode: int
    uid: int
    gid: int


@dataclass(frozen=True)
class HostConfigTranslation:
    devices: tuple[DeviceNode, ...] = ()
    env: tuple[tuple[str, str], ...] = ()


def _invalid(plugin: str, key: str, reason: str) -> HostConfigNotTranslatable:
    return HostConfigNotTranslatable(
        f"{plugin}: {key} ({reason})", extra_data={"plugin": plugin, "key": key}
    )


def _absolute(plugin: str, key: str, value: Any) -> str:
    if not isinstance(value, str) or not value.startswith("/"):
        raise _invalid(plugin, key, "must be an absolute path")
    return value


def _device_node(
    plugin: str, key: str, entry: Any, stat: Callable[[str], os.stat_result]
) -> DeviceNode:
    if not isinstance(entry, Mapping):
        raise _invalid(plugin, key, "not a mapping")
    for name in entry:
        if name not in _DEVICE_KEYS:
            raise _invalid(plugin, f"{key}.{name}", "not translatable")
    host_path = _absolute(plugin, f"{key}.PathOnHost", entry.get("PathOnHost"))
    container_path = posixpath.normpath(
        _absolute(plugin, f"{key}.PathInContainer", entry.get("PathInContainer", host_path))
    )
    if not container_path.startswith("/dev/"):
        raise _invalid(plugin, f"{key}.PathInContainer", "must be under /dev/")
    access = entry.get("CgroupPermissions", "rwm")
    if not isinstance(access, str) or not access or set(access) - set("rwm"):
        raise _invalid(plugin, f"{key}.CgroupPermissions", "must be a subset of rwm")
    try:
        st = stat(host_path)
    except OSError as e:
        raise _invalid(plugin, key, f"cannot stat {host_path}: {e}") from e
    if stat_mod.S_ISCHR(st.st_mode):
        node_type = "c"
    elif stat_mod.S_ISBLK(st.st_mode):
        node_type = "b"
    else:
        raise _invalid(plugin, key, f"{host_path} is not a character or block device")
    return DeviceNode(
        path=container_path,
        type=node_type,
        major=os.major(st.st_rdev),
        minor=os.minor(st.st_rdev),
        access=access,
        file_mode=stat_mod.S_IMODE(st.st_mode),
        uid=st.st_uid,
        gid=st.st_gid,
    )


def _env_pair(plugin: str, key: str, entry: Any) -> tuple[str, str]:
    name, sep, value = entry.partition("=") if isinstance(entry, str) else ("", "", "")
    if not sep or not name:
        raise _invalid(plugin, key, "must be NAME=VALUE")
    return name, value


def translate_fragment(
    plugin: str,
    fragment: Mapping[str, Any],
    *,
    stat: Callable[[str], os.stat_result] = os.stat,
) -> HostConfigTranslation:
    """Blocking (stat). Every key but `Env` and `HostConfig.Devices` raises, even when empty."""
    for key in fragment:
        if key not in ("Env", "HostConfig"):
            raise _invalid(plugin, str(key), "not translatable")
    host_config = fragment.get("HostConfig", {})
    if not isinstance(host_config, Mapping):
        raise _invalid(plugin, "HostConfig", "not a mapping")
    for key in host_config:
        if key != "Devices":
            raise _invalid(plugin, f"HostConfig.{key}", "not translatable")
    devices = host_config.get("Devices", ())
    if not isinstance(devices, Sequence) or isinstance(devices, (str, bytes)):
        raise _invalid(plugin, "HostConfig.Devices", "not a list")
    env = fragment.get("Env", ())
    if not isinstance(env, Sequence) or isinstance(env, (str, bytes)):
        raise _invalid(plugin, "Env", "not a list")
    return HostConfigTranslation(
        devices=tuple(
            _device_node(plugin, f"HostConfig.Devices[{i}]", entry, stat)
            for i, entry in enumerate(devices)
        ),
        env=tuple(_env_pair(plugin, f"Env[{i}]", entry) for i, entry in enumerate(env)),
    )


def merge_translations(
    translations: Sequence[tuple[str, HostConfigTranslation]],
) -> HostConfigTranslation:
    """Union in order; identical duplicates collapse, a conflicting duplicate raises."""
    devices: dict[str, tuple[str, DeviceNode]] = {}
    env: dict[str, tuple[str, str]] = {}
    for plugin, translation in translations:
        for node in translation.devices:
            owner, seen = devices.setdefault(posixpath.normpath(node.path), (plugin, node))
            if seen != node:
                raise _invalid(plugin, node.path, f"differs from the node of {owner}")
        for name, value in translation.env:
            owner, seen_value = env.setdefault(name, (plugin, value))
            if seen_value != value:
                raise _invalid(plugin, f"Env.{name}", f"differs from the value of {owner}")
    return HostConfigTranslation(
        devices=tuple(node for _, node in devices.values()),
        env=tuple((name, value) for name, (_, value) in env.items()),
    )


def apply_to_spec(
    base_spec: Mapping[str, Any], translation: HostConfigTranslation
) -> dict[str, Any]:
    """Return a copy of the spec with the device nodes and their cgroup allow rules added."""
    spec = copy.deepcopy(dict(base_spec))
    linux = spec["linux"]
    allowed: set[tuple[str, int, int, str]] = set()
    for node in translation.devices:
        linux.setdefault("devices", []).append({
            "path": node.path,
            "type": node.type,
            "major": node.major,
            "minor": node.minor,
            "fileMode": node.file_mode,
            "uid": node.uid,
            "gid": node.gid,
        })
        rule = (node.type, node.major, node.minor, node.access)
        if rule not in allowed:
            allowed.add(rule)
            linux["resources"]["devices"].append({
                "allow": True,
                "type": node.type,
                "major": node.major,
                "minor": node.minor,
                "access": node.access,
            })
    return spec
