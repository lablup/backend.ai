"""Resolve CDI device names into the container edits the containerd agent can apply."""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final, Literal

import yaml

from ai.backend.agent.errors.containerd import HostConfigNotTranslatable

CDI_SPEC_DIRS: Final = (Path("/etc/cdi"), Path("/var/run/cdi"))
_SPEC_SUFFIXES: Final = (".json", ".yaml", ".yml")
_NAME_PATTERN: Final = re.compile(r"^(?P<kind>[^/=\s]+/[^/=\s]+)=(?P<name>[^/=\s]+)$")
_SUPPORTED_EDITS: Final = frozenset({"env", "deviceNodes"})
_NODE_FIELDS: Final = frozenset({
    "path",
    "hostPath",
    "type",
    "major",
    "minor",
    "permissions",
    "fileMode",
    "uid",
    "gid",
})


@dataclass(frozen=True)
class CdiDeviceNode:
    path: str  # container path
    host_path: str  # hostPath, default path
    permissions: str  # default "rwm"
    file_mode: int | None
    uid: int | None
    gid: int | None
    type: Literal["c", "b"] | None  # if given, cross-checked against stat
    major: int | None
    minor: int | None


@dataclass(frozen=True)
class CdiEdits:
    device_nodes: tuple[CdiDeviceNode, ...]
    env: tuple[str, ...]  # "K=V"


@dataclass(frozen=True)
class _Spec:
    path: Path
    kind: str
    edits: Mapping[str, Any]
    devices: Mapping[str, Mapping[str, Any]]


def _fail(plugin: str, reason: str) -> HostConfigNotTranslatable:
    key = "HostConfig.DeviceRequests"
    return HostConfigNotTranslatable(
        f"{plugin}: {key} ({reason})", extra_data={"plugin": plugin, "key": key}
    )


def _load_specs(plugin: str, spec_dirs: Sequence[Path]) -> list[_Spec]:
    specs: list[_Spec] = []
    for spec_dir in spec_dirs:
        if not spec_dir.is_dir():
            continue
        for path in sorted(spec_dir.iterdir()):
            if path.suffix not in _SPEC_SUFFIXES or not path.is_file():
                continue
            try:
                raw = yaml.safe_load(path.read_text())
            except (OSError, yaml.YAMLError, ValueError) as e:
                raise _fail(plugin, f"unreadable CDI spec {path}: {e}") from e
            specs.append(_parse_spec(plugin, path, raw))
    return specs


def _parse_spec(plugin: str, path: Path, raw: Any) -> _Spec:
    if not isinstance(raw, Mapping) or not isinstance(raw.get("kind"), str):
        raise _fail(plugin, f"invalid CDI spec {path}")
    devices: dict[str, Mapping[str, Any]] = {}
    for device in raw.get("devices") or []:
        if not isinstance(device, Mapping) or not isinstance(device.get("name"), str):
            raise _fail(plugin, f"invalid device in CDI spec {path}")
        devices[device["name"]] = device
    edits = raw.get("containerEdits") or {}
    if not isinstance(edits, Mapping):
        raise _fail(plugin, f"invalid containerEdits in CDI spec {path}")
    return _Spec(path=path, kind=raw["kind"], edits=edits, devices=devices)


def _optional_int(plugin: str, node: Mapping[str, Any], field: str) -> int | None:
    value = node.get(field)
    if value is not None and (isinstance(value, bool) or not isinstance(value, int)):
        raise _fail(plugin, f"deviceNodes field {field} is not an integer")
    return value


def _parse_node(plugin: str, node: Any) -> CdiDeviceNode:
    if not isinstance(node, Mapping):
        raise _fail(plugin, "deviceNodes entry is not a mapping")
    unknown = set(node) - _NODE_FIELDS
    if unknown:
        raise _fail(plugin, f"unsupported deviceNodes field {sorted(unknown)[0]}")
    path = node.get("path")
    host_path = node.get("hostPath", path)
    if not isinstance(path, str) or not isinstance(host_path, str):
        raise _fail(plugin, "deviceNodes entry has no path")
    if not path.startswith("/") or not host_path.startswith("/"):
        raise _fail(plugin, "deviceNodes path and hostPath must be absolute")
    node_type = node.get("type")
    if node_type not in (None, "c", "b"):
        raise _fail(plugin, f"unsupported device node type {node_type!r}")
    permissions = node.get("permissions", "rwm")
    if not isinstance(permissions, str):
        raise _fail(plugin, "deviceNodes permissions is not a string")
    return CdiDeviceNode(
        path=path,
        host_path=host_path,
        permissions=permissions,
        file_mode=_optional_int(plugin, node, "fileMode"),
        uid=_optional_int(plugin, node, "uid"),
        gid=_optional_int(plugin, node, "gid"),
        type=node_type,
        major=_optional_int(plugin, node, "major"),
        minor=_optional_int(plugin, node, "minor"),
    )


def _apply_edits(
    plugin: str,
    edits: Mapping[str, Any],
    nodes: list[CdiDeviceNode],
    env: list[str],
) -> None:
    unsupported = set(edits) - _SUPPORTED_EDITS
    if unsupported:
        raise _fail(plugin, f"unsupported CDI container edit {sorted(unsupported)[0]}")
    for entry in edits.get("env") or []:
        if not isinstance(entry, str):
            raise _fail(plugin, "CDI env entry is not a string")
        env.append(entry)
    nodes.extend(_parse_node(plugin, node) for node in edits.get("deviceNodes") or [])


def resolve_cdi_devices(plugin: str, names: Sequence[str], spec_dirs: Sequence[Path]) -> CdiEdits:
    """Collect the env and device nodes of the named CDI devices; fails closed on anything else."""
    requested: list[tuple[str, str]] = []
    for full_name in names:
        matched = _NAME_PATTERN.match(full_name)
        if matched is None:
            raise _fail(plugin, f"malformed CDI device name {full_name!r}")
        pair = (matched["kind"], matched["name"])
        if pair not in requested:
            requested.append(pair)
    specs = _load_specs(plugin, spec_dirs)
    nodes: list[CdiDeviceNode] = []
    env: list[str] = []
    applied_specs: set[Path] = set()
    for kind, name in requested:
        found = [s for s in specs if s.kind == kind and name in s.devices]
        if not found:
            raise _fail(plugin, f"no CDI spec defines {kind}={name}")
        # FIXME(containerd-mvp): CDI gives /var/run/cdi priority; a duplicate is refused instead
        if len(found) > 1:
            raise _fail(plugin, f"{kind}={name} is defined in {found[0].path} and {found[1].path}")
        spec = found[0]
        if spec.path not in applied_specs:
            applied_specs.add(spec.path)
            _apply_edits(plugin, spec.edits, nodes, env)
        device_edits = spec.devices[name].get("containerEdits") or {}
        if not isinstance(device_edits, Mapping):
            raise _fail(plugin, f"invalid containerEdits of {kind}={name}")
        _apply_edits(plugin, device_edits, nodes, env)
    return CdiEdits(device_nodes=tuple(nodes), env=tuple(env))
