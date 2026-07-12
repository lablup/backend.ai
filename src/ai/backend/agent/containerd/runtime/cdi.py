"""Container Device Interface (CDI) resolution for the containerd OCI spec (BEP-1062).

The low-level containerd ``Containers.Create`` path does NOT resolve CDI device references —
only the CRI plugin, dockerd, or the containerd Go client's ``oci.WithCDIDevices`` do. Since we
build the OCI runtime spec ourselves and hand it straight to runc, we resolve CDI here: load the
host's CDI specs, look up a fully-qualified device (e.g. ``nvidia.com/gpu=0``), and translate its
``containerEdits`` (device nodes, mounts, hooks, env) into OCI runtime-spec fields. runc then
consumes a plain, fully-resolved spec — no CDI awareness needed in the runtime.

This is the vendor-neutral path: any device a CDI spec describes (NVIDIA GPU, AMD GPU, NPU, ...)
is injected the same way, and the per-vendor details live in the toolkit-generated CDI spec
instead of being hardcoded here.

Only ``load_device_edits`` touches the filesystem; resolution and OCI translation are pure.
"""

from __future__ import annotations

import json
import os
import stat
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

import yaml

# CDI spec search path (static + generated), highest precedence last (mirrors the CDI spec).
CDI_DEFAULT_DIRS: tuple[str, ...] = ("/etc/cdi", "/var/run/cdi")

_OCI_HOOK_NAMES = frozenset({
    "prestart",
    "createRuntime",
    "createContainer",
    "startContainer",
    "poststart",
    "poststop",
})
_EDIT_KEYS = ("deviceNodes", "mounts", "hooks", "env")


def _merge_edits(spec_level: Mapping[str, Any], device: Mapping[str, Any]) -> dict[str, list[Any]]:
    """A device's effective edits are the spec-level containerEdits followed by the device's own."""
    return {key: [*(spec_level.get(key) or []), *(device.get(key) or [])] for key in _EDIT_KEYS}


def load_device_edits(dirs: Sequence[str] = CDI_DEFAULT_DIRS) -> dict[str, dict[str, list[Any]]]:
    """Load every CDI spec under ``dirs`` into ``{"<vendor>/<class>=<name>": merged edits}``.

    Malformed/unreadable specs are skipped; later files override earlier ones for the same
    device name. Returns an empty map when no specs exist (the caller then falls back)."""
    result: dict[str, dict[str, list[Any]]] = {}
    for d in dirs:
        base = Path(d)
        if not base.is_dir():
            continue
        for f in sorted(base.iterdir()):
            if f.suffix not in (".yaml", ".yml", ".json"):
                continue
            try:
                text = f.read_text()
                spec = json.loads(text) if f.suffix == ".json" else yaml.safe_load(text)
            except (OSError, ValueError):
                continue
            if not isinstance(spec, dict) or not (kind := spec.get("kind")):
                continue
            spec_edits = spec.get("containerEdits") or {}
            for dev in spec.get("devices") or []:
                if (name := dev.get("name")) is None:
                    continue
                result[f"{kind}={name}"] = _merge_edits(spec_edits, dev.get("containerEdits") or {})
    return result


def _device_node_to_oci(dn: Mapping[str, Any]) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    """Translate a CDI deviceNode to (OCI linux.device, cgroup device rule). Major/minor/type are
    filled by stat()ing the host node when the spec omits them (as the CDI spec permits)."""
    path = dn.get("path")
    if not path:
        return None, {}
    major, minor, dev_type = dn.get("major"), dn.get("minor"), dn.get("type")
    if major is None or minor is None or dev_type is None:
        try:
            st = Path(dn.get("hostPath") or path).stat()
        except OSError:
            return None, {}
        if major is None:
            major = os.major(st.st_rdev)
        if minor is None:
            minor = os.minor(st.st_rdev)
        if dev_type is None:
            dev_type = "b" if stat.S_ISBLK(st.st_mode) else "c"
    oci_dev: dict[str, Any] = {"path": path, "type": dev_type, "major": major, "minor": minor}
    for key in ("fileMode", "uid", "gid"):
        if dn.get(key) is not None:
            oci_dev[key] = dn[key]
    rule = {
        "allow": True,
        "type": dev_type,
        "major": major,
        "minor": minor,
        "access": dn.get("permissions") or "rwm",
    }
    return oci_dev, rule


def _mount_to_oci(m: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "destination": m["containerPath"],
        "source": m["hostPath"],
        "type": m.get("type") or "bind",
        "options": list(m.get("options") or ["rbind", "ro"]),
    }


def _add_hook(hooks: dict[str, list[dict[str, Any]]], h: Mapping[str, Any]) -> None:
    name = h.get("hookName")
    if name not in _OCI_HOOK_NAMES or not h.get("path"):
        return
    entry: dict[str, Any] = {"path": h["path"], "args": list(h.get("args") or [])}
    if h.get("env"):
        entry["env"] = list(h["env"])
    if h.get("timeout") is not None:
        entry["timeout"] = h["timeout"]
    hooks.setdefault(name, []).append(entry)


def apply_device_edits(spec: dict[str, Any], edits_list: Sequence[Mapping[str, Any]]) -> None:
    """Merge resolved CDI edits into an OCI *runtime* spec in place: deviceNodes ->
    linux.devices + cgroup device rules, mounts -> mounts, hooks -> hooks, env -> process.env.
    Device paths and env keys are de-duplicated; env values from CDI override existing keys."""
    linux = spec.setdefault("linux", {})
    devices: list[dict[str, Any]] = linux.setdefault("devices", [])
    dev_rules: list[dict[str, Any]] = linux.setdefault("resources", {}).setdefault("devices", [])
    mounts: list[dict[str, Any]] = spec.setdefault("mounts", [])
    env: list[str] = spec.setdefault("process", {}).setdefault("env", [])
    hooks: dict[str, list[dict[str, Any]]] = spec.setdefault("hooks", {})

    seen_dev = {d["path"] for d in devices}
    for edits in edits_list:
        for dn in edits.get("deviceNodes") or []:
            oci_dev, rule = _device_node_to_oci(dn)
            if oci_dev is None or oci_dev["path"] in seen_dev:
                continue
            seen_dev.add(oci_dev["path"])
            devices.append(oci_dev)
            dev_rules.append(rule)
        mounts.extend(_mount_to_oci(m) for m in edits.get("mounts") or [])
        for raw in edits.get("env") or []:
            key = str(raw).split("=", 1)[0]
            env[:] = [e for e in env if e.split("=", 1)[0] != key]
            env.append(str(raw))
        for h in edits.get("hooks") or []:
            _add_hook(hooks, h)


def inject_cdi_devices(
    spec: dict[str, Any], qualified_names: Sequence[str], *, dirs: Sequence[str] = CDI_DEFAULT_DIRS
) -> bool:
    """Resolve each fully-qualified CDI device and inject its edits into the OCI runtime ``spec``.

    Returns True only if EVERY name resolves (and was applied); returns False without mutating
    ``spec`` if any device is unknown, so the caller can fall back to another injection path.
    """
    device_map = load_device_edits(dirs)
    resolved: list[dict[str, list[Any]]] = []
    for name in qualified_names:
        edits = device_map.get(name)
        if edits is None:
            return False
        resolved.append(edits)
    apply_device_edits(spec, resolved)
    return True
