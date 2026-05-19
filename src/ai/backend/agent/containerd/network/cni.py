"""Generic CNI plugin-chain invoker.

This module is provider-agnostic: it speaks the CNI specification — exec a
plugin binary with ``CNI_*`` environment variables and a JSON network
config on stdin, read the result JSON from stdout — and is shared by every
``NetworkProvider``. Cilium-, Calico-, bridge-specific behaviour lives in
the providers, not here: all CNI plugins conform to the same exec protocol,
so re-abstracting it per provider would be pointless duplication.

A CNI conflist is ``{name, cniVersion, plugins: [...]}``. ``ADD`` runs the
plugins in order, threading each plugin's result into the next as
``prevResult``; ``DEL`` runs them in reverse. The final ADD plugin's
result is the overall network result.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from ai.backend.agent.errors.containerd import CniInvocationError
from ai.backend.logging import BraceStyleAdapter

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

DEFAULT_CNI_BIN_DIR = Path("/opt/cni/bin")
DEFAULT_CNI_CONF_DIR = Path("/etc/cni/net.d")
DEFAULT_IFNAME = "eth0"


def load_conflist(name: str, *, conf_dir: Path = DEFAULT_CNI_CONF_DIR) -> dict[str, Any]:
    """Load the CNI conflist whose ``name`` field equals ``name``.

    Conflists are matched by their ``name`` field, not filename, mirroring
    how the CRI plugin / kubelet select a network.
    """
    if not conf_dir.is_dir():
        raise CniInvocationError(f"CNI conf dir {conf_dir} does not exist")
    for entry in sorted(conf_dir.iterdir()):
        if entry.suffix != ".conflist" or not entry.is_file():
            continue
        try:
            document = json.loads(entry.read_text())
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(document, dict) and document.get("name") == name:
            return document
    raise CniInvocationError(f"No CNI conflist named '{name}' found under {conf_dir}")


class CniInvoker:
    """Runs a CNI plugin chain against a network namespace."""

    def __init__(self, *, bin_dir: Path = DEFAULT_CNI_BIN_DIR) -> None:
        self._bin_dir = bin_dir

    async def add(
        self,
        conflist: Mapping[str, Any],
        *,
        container_id: str,
        netns_path: str,
        ifname: str = DEFAULT_IFNAME,
        cni_args: Mapping[str, str] | None = None,
    ) -> dict[str, Any]:
        """Run the conflist's plugin chain with ``CNI_COMMAND=ADD``.

        Returns the final plugin's CNI result (``interfaces`` / ``ips`` /
        ``routes`` / ``dns``).
        """
        result: dict[str, Any] = {}
        for plugin in self._plugins(conflist):
            result = await self._exec(
                command="ADD",
                conflist=conflist,
                plugin=plugin,
                prev_result=result or None,
                container_id=container_id,
                netns_path=netns_path,
                ifname=ifname,
                cni_args=cni_args,
            )
        return result

    async def delete(
        self,
        conflist: Mapping[str, Any],
        *,
        container_id: str,
        netns_path: str,
        ifname: str = DEFAULT_IFNAME,
        cni_args: Mapping[str, str] | None = None,
    ) -> None:
        """Run the conflist's plugin chain with ``CNI_COMMAND=DEL`` (reverse order)."""
        for plugin in reversed(self._plugins(conflist)):
            await self._exec(
                command="DEL",
                conflist=conflist,
                plugin=plugin,
                prev_result=None,
                container_id=container_id,
                netns_path=netns_path,
                ifname=ifname,
                cni_args=cni_args,
            )

    @staticmethod
    def _plugins(conflist: Mapping[str, Any]) -> list[dict[str, Any]]:
        plugins = conflist.get("plugins")
        if not isinstance(plugins, list) or not plugins:
            raise CniInvocationError(f"CNI conflist '{conflist.get('name')}' has no 'plugins' list")
        return plugins

    async def _exec(
        self,
        *,
        command: str,
        conflist: Mapping[str, Any],
        plugin: Mapping[str, Any],
        prev_result: Mapping[str, Any] | None,
        container_id: str,
        netns_path: str,
        ifname: str,
        cni_args: Mapping[str, str] | None,
    ) -> dict[str, Any]:
        plugin_type = plugin.get("type")
        if not plugin_type:
            raise CniInvocationError("a CNI conflist plugin entry has no 'type'")
        binary = self._bin_dir / str(plugin_type)

        # The network config handed to a plugin on stdin is its own object
        # from the conflist, plus the conflist-level cniVersion/name, plus
        # the previous plugin's result chained in as prevResult.
        netconf: dict[str, Any] = dict(plugin)
        netconf["cniVersion"] = conflist.get("cniVersion", "")
        netconf["name"] = conflist.get("name", "")
        if prev_result is not None:
            netconf["prevResult"] = dict(prev_result)
        stdin = json.dumps(netconf).encode()

        env = dict(os.environ)
        env.update(
            CNI_COMMAND=command,
            CNI_CONTAINERID=container_id,
            CNI_NETNS=netns_path,
            CNI_IFNAME=ifname,
            CNI_PATH=str(self._bin_dir),
        )
        if cni_args:
            env["CNI_ARGS"] = ";".join(f"{key}={value}" for key, value in cni_args.items())

        log.debug("CNI {} via plugin '{}' for {}", command, plugin_type, container_id)
        try:
            proc = await asyncio.create_subprocess_exec(
                str(binary),
                env=env,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
        except OSError as exc:
            raise CniInvocationError(
                f"Could not execute CNI plugin '{plugin_type}' ({binary}): {exc}"
            ) from exc
        stdout, stderr = await proc.communicate(stdin)
        if proc.returncode != 0:
            raise CniInvocationError(
                f"CNI plugin '{plugin_type}' {command} failed "
                f"(exit {proc.returncode}): {_cni_error(stdout, stderr)}"
            )
        text = stdout.decode(errors="replace").strip()
        if not text:
            # DEL and some plugins legitimately produce no result.
            return {}
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError as exc:
            raise CniInvocationError(
                f"CNI plugin '{plugin_type}' {command} returned invalid JSON: {exc}"
            ) from exc
        if not isinstance(parsed, dict):
            raise CniInvocationError(
                f"CNI plugin '{plugin_type}' {command} returned a non-object result"
            )
        return parsed


def _cni_error(stdout: bytes, stderr: bytes) -> str:
    """Extract a human-readable error from a failed CNI plugin invocation.

    CNI plugins report errors as a JSON ``{code, msg, details}`` document
    on stdout; fall back to stderr text when that is unavailable.
    """
    text = stdout.decode(errors="replace").strip()
    document: Any = None
    try:
        document = json.loads(text)
    except json.JSONDecodeError:
        document = None
    if isinstance(document, dict) and document.get("msg"):
        message = str(document["msg"])
        details = document.get("details")
        return f"{message}: {details}" if details else message
    return text or stderr.decode(errors="replace").strip() or "(no error output)"
