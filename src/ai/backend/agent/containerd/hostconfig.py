"""Translate a compute plugin's Docker container fragment into OCI spec edits."""

from __future__ import annotations

import copy
import os
import re
import stat as stat_mod
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final, Literal

from ai.backend.agent.containerd.cdi import CDI_SPEC_DIRS, CdiDeviceNode, resolve_cdi_devices
from ai.backend.agent.containerd.profile.base import TranslatedDevice
from ai.backend.agent.errors.containerd import HostConfigNotTranslatable

_RLIM_INFINITY: Final = 2**64 - 1
_TOP_LEVEL_KEYS: Final = frozenset({"Env", "HostConfig"})
_HOST_CONFIG_KEYS: Final = frozenset({"Devices", "CapAdd", "Ulimits", "IpcMode", "DeviceRequests"})
_DEVICE_KEYS: Final = frozenset({"PathOnHost", "PathInContainer", "CgroupPermissions"})
_REQUEST_KEYS: Final = frozenset({"Driver", "DeviceIDs", "Count", "Capabilities", "Options"})
_ULIMIT_KEYS: Final = frozenset({"Name", "Soft", "Hard"})
_ULIMIT_NAMES: Final = frozenset({
    "as",
    "core",
    "cpu",
    "data",
    "fsize",
    "locks",
    "memlock",
    "msgqueue",
    "nice",
    "nofile",
    "nproc",
    "rss",
    "rtprio",
    "rttime",
    "sigpending",
    "stack",
})
_CAP_PATTERN: Final = re.compile(r"^CAP_[A-Z0-9_]+$")
_ACCESS_ORDER: Final = "rwm"


@dataclass(frozen=True)
class DeviceNode:
    device: TranslatedDevice  # path = PathInContainer; access = CgroupPermissions
    host_path: str
    file_mode: int  # permission bits of the host node (Docker parity)
    uid: int
    gid: int


@dataclass(frozen=True)
class Rlimit:
    type: str  # "RLIMIT_MEMLOCK"
    soft: int  # -1 already mapped to 2**64-1
    hard: int


@dataclass(frozen=True)
class HostConfigTranslation:
    devices: tuple[DeviceNode, ...] = ()
    capabilities: tuple[str, ...] = ()  # "CAP_"-prefixed, upper case
    rlimits: tuple[Rlimit, ...] = ()
    env: tuple[tuple[str, str], ...] = ()  # in emission order
    host_ipc: bool = False

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
    cdi: CdiDeviceNode | None = None,
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
    if cdi is not None:
        if (
            (cdi.type is not None and cdi.type != node_type)
            or cdi.major not in (None, major)
            or cdi.minor not in (None, minor)
        ):
            raise _refuse(plugin, key, f"CDI node {host_path} does not match the host device")
        file_mode = file_mode if cdi.file_mode is None else cdi.file_mode
        uid = uid if cdi.uid is None else cdi.uid
        gid = gid if cdi.gid is None else cdi.gid
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


def _translate_caps(plugin: str, entries: Sequence[Any]) -> list[HostConfigTranslation]:
    caps: list[str] = []
    for i, entry in enumerate(entries):
        key = f"HostConfig.CapAdd[{i}]"
        if not isinstance(entry, str) or not entry:
            raise _refuse(plugin, key, "not a capability name")
        name = entry.upper()
        if not name.startswith("CAP_"):
            name = f"CAP_{name}"
        if name == "CAP_ALL" or not _CAP_PATTERN.match(name):
            raise _refuse(plugin, key, f"invalid capability {entry!r}")
        caps.append(name)
    return [HostConfigTranslation(capabilities=tuple(caps))]


def _int_limit(plugin: str, key: str, value: Any) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < -1:
        raise _refuse(plugin, key, "must be an integer, -1 for unlimited")
    return _RLIM_INFINITY if value == -1 else value


def _translate_ulimits(plugin: str, entries: Sequence[Any]) -> list[HostConfigTranslation]:
    out: list[HostConfigTranslation] = []
    for i, entry in enumerate(entries):
        base = f"HostConfig.Ulimits[{i}]"
        item = _mapping(plugin, base, entry)
        _check_keys(plugin, base, item, _ULIMIT_KEYS)
        name = item.get("Name")
        if not isinstance(name, str) or name.lower() not in _ULIMIT_NAMES:
            raise _refuse(plugin, f"{base}.Name", "unknown ulimit")
        # FIXME(containerd-mvp): plugin ulimits are not clamped by get_safe_ulimit
        soft = _int_limit(plugin, f"{base}.Soft", item.get("Soft"))
        hard = _int_limit(plugin, f"{base}.Hard", item.get("Hard"))
        if soft > hard:
            raise _refuse(plugin, base, "Soft exceeds Hard")
        out.append(HostConfigTranslation(rlimits=(Rlimit(f"RLIMIT_{name.upper()}", soft, hard),)))
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


def _translate_requests(
    plugin: str,
    entries: Sequence[Any],
    stat: Callable[[str], os.stat_result],
    cdi_spec_dirs: Sequence[Path],
) -> list[HostConfigTranslation]:
    out: list[HostConfigTranslation] = []
    for i, entry in enumerate(entries):
        base = f"HostConfig.DeviceRequests[{i}]"
        item = _mapping(plugin, base, entry)
        _check_keys(plugin, base, item, _REQUEST_KEYS)
        if item.get("Driver") != "cdi":
            raise _refuse(plugin, f"{base}.Driver", "only the cdi driver is translatable")
        ids = _sequence(plugin, f"{base}.DeviceIDs", item.get("DeviceIDs"))
        if not ids or not all(isinstance(name, str) for name in ids):
            raise _refuse(plugin, f"{base}.DeviceIDs", "must be a non-empty list of names")
        if item.get("Count") not in (None, 0) or isinstance(item.get("Count"), bool):
            raise _refuse(plugin, f"{base}.Count", "must be 0")
        if item.get("Capabilities") not in (None, []):
            raise _refuse(plugin, f"{base}.Capabilities", "must be empty")
        if item.get("Options") not in (None, {}):
            raise _refuse(plugin, f"{base}.Options", "must be empty")
        edits = resolve_cdi_devices(plugin, list(ids), cdi_spec_dirs)
        for cdi_node in edits.device_nodes:
            access = _validate_access(plugin, base, cdi_node.permissions)
            node = _device_node(
                plugin, base, cdi_node.host_path, cdi_node.path, access, stat, cdi_node
            )
            out.append(HostConfigTranslation(devices=(node,)))
        out.extend(_translate_env(plugin, list(edits.env), f"{base}.cdi.env"))
    return out


def translate_fragment(
    plugin: str,
    fragment: Mapping[str, Any],
    *,
    stat: Callable[[str], os.stat_result] = os.stat,
    cdi_spec_dirs: Sequence[Path] = CDI_SPEC_DIRS,
) -> HostConfigTranslation:
    """Blocking (stat, CDI reads). Every key without an OCI translation raises."""
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
    if "CapAdd" in host_config:
        entries = _sequence(plugin, "HostConfig.CapAdd", host_config["CapAdd"])
        parts.extend(_translate_caps(plugin, entries))
    if "Ulimits" in host_config:
        entries = _sequence(plugin, "HostConfig.Ulimits", host_config["Ulimits"])
        parts.extend(_translate_ulimits(plugin, entries))
    if "IpcMode" in host_config:
        # FIXME(containerd-mvp): IpcMode host does not bind-mount the host /dev/shm
        if host_config["IpcMode"] != "host":
            raise _refuse(plugin, "HostConfig.IpcMode", "only host is translatable")
        parts.append(HostConfigTranslation(host_ipc=True))
    if "DeviceRequests" in host_config:
        entries = _sequence(plugin, "HostConfig.DeviceRequests", host_config["DeviceRequests"])
        parts.extend(_translate_requests(plugin, entries, stat, cdi_spec_dirs))
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
    rlimits: dict[str, tuple[str, Rlimit]] = {}
    caps: list[str] = []
    host_ipc = False
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
        for rlimit in translation.rlimits:
            if rlimit.type in rlimits and rlimits[rlimit.type][1] != rlimit:
                raise _conflict(
                    rlimits[rlimit.type][0],
                    plugin,
                    f"HostConfig.Ulimits.{rlimit.type}",
                    "set different limits",
                )
            rlimits.setdefault(rlimit.type, (plugin, rlimit))
        caps.extend(c for c in translation.capabilities if c not in caps)
        host_ipc = host_ipc or translation.host_ipc
    return HostConfigTranslation(
        devices=tuple(node for _, node in devices.values()),
        capabilities=tuple(caps),
        rlimits=tuple(r for _, r in rlimits.values()),
        env=tuple((name, value) for name, (_, value) in env.items()),
        host_ipc=host_ipc,
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
    process = spec["process"]
    for name in ("bounding", "effective", "permitted"):
        current = process["capabilities"][name]
        current.extend(c for c in translation.capabilities if c not in current)
    for rlimit in translation.rlimits:
        entry = {"type": rlimit.type, "soft": rlimit.soft, "hard": rlimit.hard}
        for i, existing in enumerate(process["rlimits"]):
            if existing["type"] == rlimit.type:
                process["rlimits"][i] = entry
                break
        else:
            process["rlimits"].append(entry)
    if translation.host_ipc:
        linux["namespaces"] = [ns for ns in linux["namespaces"] if ns["type"] != "ipc"]
    return spec
