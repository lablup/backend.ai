"""
Containerd backend startup pre-flight checks.

Runs once at agent startup, before any kernel work, to fail fast on
CNI / containerd misconfigurations that would otherwise surface as
opaque sandbox-creation failures or — worse — as silently unreachable
service ports.

All filesystem I/O is dispatched to a worker thread via
``asyncio.to_thread`` so the agent's event loop stays responsive.
"""

from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path
from typing import Any

from ai.backend.agent.config.unified import (
    ContainerdContainerConfig,
    ContainerdNetworkMode,
)
from ai.backend.agent.errors.containerd import (
    CniBinaryMissingError,
    CniConfDirNotWritableError,
    CniConflistInvalidError,
    CniConflistMissingError,
    CniPortmapMissingError,
)

REQUIRED_CNI_BINARIES: tuple[str, ...] = (
    "bridge",
    "portmap",
    "host-local",
    "loopback",
)


async def run_preflight(config: ContainerdContainerConfig) -> None:
    """Dispatch pre-flight checks based on the configured network mode."""
    network = config.network
    match network.mode:
        case ContainerdNetworkMode.NONE:
            return
        case ContainerdNetworkMode.MANAGED:
            await _check_cni_binaries(network.cni_bin_dir)
            await _check_managed_dir_writable(network.cni_conf_dir)
        case ContainerdNetworkMode.HOST:
            await _check_cni_binaries(network.cni_bin_dir)
            conflist = await _load_named_conflist(network.cni_conf_dir, network.network_name)
            _check_portmap_chained(conflist, network.network_name)


async def _check_cni_binaries(cni_bin_dir: Path) -> None:
    missing = await asyncio.to_thread(_collect_missing_binaries, cni_bin_dir)
    if missing:
        raise CniBinaryMissingError(
            f"CNI plugin binaries missing in {cni_bin_dir}: {', '.join(missing)}. "
            "Install the host's containernetworking-plugins package "
            "(or set [container.containerd.network].cni_bin_dir to the correct path)."
        )


def _collect_missing_binaries(cni_bin_dir: Path) -> list[str]:
    return [name for name in REQUIRED_CNI_BINARIES if not (cni_bin_dir / name).is_file()]


async def _check_managed_dir_writable(cni_conf_dir: Path) -> None:
    ok = await asyncio.to_thread(_is_dir_writable, cni_conf_dir)
    if not ok:
        raise CniConfDirNotWritableError(
            f"CNI conf dir {cni_conf_dir} is not writable by the agent. "
            "In 'managed' mode the agent generates a conflist into this directory; "
            "create it with appropriate permissions or switch network mode."
        )


def _is_dir_writable(path: Path) -> bool:
    if not path.exists():
        try:
            path.mkdir(parents=True, exist_ok=True)
        except OSError:
            return False
    return path.is_dir() and os.access(path, os.W_OK)


async def _load_named_conflist(cni_conf_dir: Path, network_name: str) -> dict[str, Any]:
    raw = await asyncio.to_thread(_read_named_conflist, cni_conf_dir, network_name)
    if raw is None:
        raise CniConflistMissingError(
            f"No CNI conflist with name='{network_name}' found in {cni_conf_dir}. "
            "In 'host' mode the agent expects an operator-supplied conflist; "
            "set [container.containerd.network].network_name to one that exists, "
            "or switch to 'managed' mode."
        )
    try:
        parsed: dict[str, Any] = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise CniConflistInvalidError(
            f"CNI conflist for network='{network_name}' in {cni_conf_dir} is not valid JSON: {exc}"
        ) from exc
    return parsed


def _read_named_conflist(cni_conf_dir: Path, network_name: str) -> str | None:
    if not cni_conf_dir.is_dir():
        return None
    for entry in sorted(cni_conf_dir.iterdir()):
        if entry.suffix != ".conflist" or not entry.is_file():
            continue
        try:
            text = entry.read_text()
            doc = json.loads(text)
        except (OSError, json.JSONDecodeError):
            continue
        if doc.get("name") == network_name:
            return text
    return None


def _check_portmap_chained(conflist: dict[str, Any], network_name: str) -> None:
    plugins = conflist.get("plugins", [])
    if not isinstance(plugins, list):
        raise CniConflistInvalidError(
            f"CNI conflist '{network_name}' has a non-list 'plugins' field."
        )
    if not any(isinstance(p, dict) and p.get("type") == "portmap" for p in plugins):
        raise CniPortmapMissingError(
            f"CNI conflist '{network_name}' does not chain the 'portmap' plugin. "
            "Backend.AI service ports (Jupyter, SSH, TensorBoard, ...) require "
            "portmap for host-port forwarding; without it, the App Proxy cannot "
            "reach kernel containers."
        )
