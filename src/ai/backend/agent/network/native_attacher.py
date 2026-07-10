"""Native veth/bridge attach runner (BEP-1058) — replaces the CNI ``bridge`` plugin binary.

The BEP-1058 data plane is host-native: the session fabric (vxlan device, bridge, FDB/ARP)
is built with plain iproute2. The only remaining ``/opt/cni/bin`` dependency was the
per-container *attach* step, which this module reimplements over ``ip``/``iptables`` so no
external cni-plugins package is required.

It is a drop-in ``CniRunner`` (same ``(command, *, ifname, netns, container_id, config)``
signature and CNI-result shape), honouring the same bridge config semantics the backends
already emit: bridge attach + MTU, static or host-local IPAM, ``isGateway`` (gateway IP on the
bridge), ``isDefaultGateway`` (default route in the container) and ``ipMasq`` (egress NAT).
"""

from __future__ import annotations

import asyncio
import hashlib
import ipaddress
import logging
import re
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from ai.backend.agent.errors.network import (
    NetworkStateStoreConflict,
    SubnetAddressPoolExhausted,
)
from ai.backend.logging import BraceStyleAdapter

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

_DEFAULT_IPAM_STATE_DIR = Path("/var/lib/backend.ai/net-ipam")
_NETNS_PID_RE = re.compile(r"/proc/(\d+)/ns/net")


async def _run(argv: Sequence[str], *, check: bool = True) -> tuple[int, bytes, bytes]:
    proc = await asyncio.create_subprocess_exec(
        *argv, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
    out, err = await proc.communicate()
    rc = proc.returncode or 0
    if check and rc != 0:
        raise RuntimeError(
            f"command failed (rc={rc}): {' '.join(argv)}: {err.decode(errors='replace').strip()}"
        )
    return rc, out, err


def _pid_from_netns(netns: str) -> str:
    m = _NETNS_PID_RE.match(netns)
    if not m:
        raise ValueError(f"unsupported netns path (expected /proc/<pid>/ns/net): {netns}")
    return m.group(1)


def _veth_name(container_id: str, ifname: str, side: str) -> str:
    # <=15-char, deterministic, collision-safe interface name for the veth ends.
    return "bai" + hashlib.sha1(f"{container_id}/{ifname}/{side}".encode()).hexdigest()[:11]


# One IPAM per store, per process — see HostLocalIpam's docstring.
_ipams: dict[Path, HostLocalIpam] = {}


def get_host_local_ipam(state_dir: Path | None = None) -> HostLocalIpam:
    """The process-wide IPAM owning ``state_dir``. Construct the class directly only in tests,
    where each case owns its own store."""
    resolved = state_dir if state_dir is not None else _DEFAULT_IPAM_STATE_DIR
    if (existing := _ipams.get(resolved)) is not None:
        return existing
    ipam = HostLocalIpam(resolved)
    _ipams[resolved] = ipam
    return ipam


class HostLocalIpam:
    """Per-subnet IP allocator, journalled to disk (the CNI host-local plugin's store layout).

    The authoritative state is in memory; ``<state_dir>/<subnet>/<ip>`` — a file whose content is
    the owning ``<container_id>/<ifname>`` — is its journal, replayed once per subnet on first
    touch so allocations survive an agent restart. Allocation is idempotent per owner.

    A store has one writer per node and one owner per process (`get_host_local_ipam`), so no
    locking beyond the in-process mutex is needed or attempted: a second writer would already be
    deleting and recreating this node's bridges. An address that exists on disk while the owner
    believes it free means that has happened, and raises rather than being allocated around.
    See `ai.backend.agent.network.local_subnet` for the same design, stated at length."""

    _dir: Path
    _lock: asyncio.Lock
    # subnet dir -> {owner -> ip}, authoritative once the subnet has been replayed
    _owners: dict[Path, dict[str, str]]

    def __init__(self, state_dir: Path) -> None:
        self._dir = state_dir
        self._lock = asyncio.Lock()
        self._owners = {}

    def _subnet_dir(self, subnet: str) -> Path:
        return self._dir / subnet.replace("/", "_")

    def _replay(self, d: Path) -> dict[str, str]:
        """Rebuild owner -> ip from the journal. An owner recorded at two addresses (only possible
        in a store written by an older, racy runner) resolves deterministically to the first by
        sorted file name — the same first-wins-by-name rule as LocalSubnetAllocator._replay,
        instead of the previous iteration-order nondeterminism."""
        if not d.is_dir():
            return {}
        owners: dict[str, str] = {}
        for f in sorted(d.iterdir(), key=lambda p: p.name):
            if f.is_file():
                owners.setdefault(f.read_text().strip(), f.name)
        return owners

    async def _owners_of(self, d: Path) -> dict[str, str]:
        if (loaded := self._owners.get(d)) is not None:
            return loaded
        replayed = await asyncio.to_thread(self._replay, d)
        self._owners[d] = replayed
        return replayed

    def _write_claim(self, d: Path, ip: str, owner: str) -> None:
        d.mkdir(parents=True, exist_ok=True)
        try:
            with (d / ip).open("x") as f:
                f.write(owner)
        except FileExistsError as e:
            raise NetworkStateStoreConflict(
                f"address {ip} exists on disk but is free in memory (store: {d}) — "
                f"another writer owns this node's network"
            ) from e

    async def allocate(
        self, subnet: str, container_id: str, ifname: str, *, reserve: Sequence[str]
    ) -> str:
        owner = f"{container_id}/{ifname}"
        async with self._lock:
            d = self._subnet_dir(subnet)
            owners = await self._owners_of(d)
            if (existing := owners.get(owner)) is not None:
                return existing  # idempotent re-ADD
            used = set(owners.values()) | set(reserve)
            for host in ipaddress.ip_network(subnet).hosts():
                ip = str(host)
                if ip in used:
                    continue
                # Journal before the caller wires up the veth, and only then commit to memory.
                await asyncio.to_thread(self._write_claim, d, ip, owner)
                owners[owner] = ip
                return ip
            raise SubnetAddressPoolExhausted(f"no free address left in {subnet}")

    def subnets(self) -> list[str]:
        """Every subnet the journal holds records for, as the CIDR string it was keyed by."""
        if not self._dir.is_dir():
            return []
        return [d.name.replace("_", "/") for d in self._dir.iterdir() if d.is_dir()]

    async def owners(self, subnet: str) -> dict[str, str]:
        """``{container_id/ifname: ip}`` for one subnet. Restart recovery diffs the owners against
        the live containers to reclaim addresses (and their host veths) left by containers that
        died while the agent was down."""
        async with self._lock:
            return dict(await self._owners_of(self._subnet_dir(subnet)))

    async def release(self, subnet: str, container_id: str, ifname: str) -> int:
        """Release this owner's address; return the number of addresses still allocated."""
        owner = f"{container_id}/{ifname}"
        async with self._lock:
            d = self._subnet_dir(subnet)
            owners = await self._owners_of(d)
            ip = owners.get(owner)
            if ip is None:
                return len(owners)
            # Drop the record first: a failed unlink must not leave memory handing the address
            # out again while the journal still names this owner.
            await asyncio.to_thread((d / ip).unlink, True)
            del owners[owner]
            return len(owners)


class NativeBridgeAttachRunner:
    """Drop-in ``CniRunner`` that attaches/detaches a container to a bridge natively."""

    _ipam: HostLocalIpam

    def __init__(self, *, ipam_state_dir: Path = _DEFAULT_IPAM_STATE_DIR) -> None:
        # The process-wide owner: every agent this runtime hosts shares one node-local IP space.
        self._ipam = get_host_local_ipam(ipam_state_dir)

    async def __call__(
        self,
        command: str,
        *,
        ifname: str,
        netns: str,
        container_id: str,
        config: Mapping[str, Any],
    ) -> dict[str, Any] | None:
        if command == "ADD":
            return await self._add(ifname, netns, container_id, config)
        if command == "DEL":
            await self._del(ifname, container_id, config)
            return None
        raise ValueError(f"unsupported CNI command: {command}")

    async def _resolve_ip(
        self, ifname: str, container_id: str, ipam: Mapping[str, Any]
    ) -> tuple[str, str, str | None, str | None]:
        """Return (ip, prefixlen, gateway, subnet); gateway/subnet are None for static IPAM."""
        if ipam.get("type") == "static":
            cidr = ipam["addresses"][0]["address"]
            ip, prefix = cidr.split("/")
            return ip, prefix, None, None
        subnet = ipam["subnet"]
        network = ipaddress.ip_network(subnet)
        gateway = str(next(iter(network.hosts())))  # first host == the bridge gateway
        ip = await self._ipam.allocate(subnet, container_id, ifname, reserve=[gateway])
        return ip, str(network.prefixlen), gateway, subnet

    async def _add(
        self, ifname: str, netns: str, container_id: str, config: Mapping[str, Any]
    ) -> dict[str, Any]:
        bridge = str(config["bridge"])
        mtu = str(int(config.get("mtu") or 1500))
        ipam = config.get("ipam") or {}
        ip, prefix, gateway, subnet = await self._resolve_ip(ifname, container_id, ipam)

        gw_on_bridge = f"{gateway}/{prefix}" if config.get("isGateway") and gateway else None
        await self._ensure_bridge(bridge, mtu, gw_on_bridge)

        pid = _pid_from_netns(netns)
        host_veth = _veth_name(container_id, ifname, "h")
        tmp_veth = _veth_name(container_id, ifname, "c")
        rc, _, _ = await _run(["ip", "link", "show", host_veth], check=False)
        if rc != 0:  # not yet attached
            await _run([
                "ip", "link", "add", host_veth, "mtu", mtu,
                "type", "veth", "peer", "name", tmp_veth, "mtu", mtu,
            ])  # fmt: skip
            await _run(["ip", "link", "set", tmp_veth, "netns", pid])
            await _run(["ip", "link", "set", host_veth, "master", bridge])
            await _run(["ip", "link", "set", host_veth, "up"])
            ns = ["nsenter", "--net=" + netns, "--"]
            await _run(ns + ["ip", "link", "set", tmp_veth, "name", ifname])
            # Pin the NIC's MAC when the config specifies one (overlay endpoints): peers program
            # FDB/ARP to this exact address, so the container NIC must own it or inbound unicast
            # is dropped. Set while the link is down, before bringing it up.
            if mac := config.get("mac"):
                await _run(ns + ["ip", "link", "set", ifname, "address", str(mac)])
            await _run(ns + ["ip", "addr", "add", f"{ip}/{prefix}", "dev", ifname])
            await _run(ns + ["ip", "link", "set", ifname, "up"])
            await _run(ns + ["ip", "link", "set", "lo", "up"], check=False)
            if config.get("isDefaultGateway") and gateway:
                await _run(ns + ["ip", "route", "replace", "default", "via", gateway], check=False)

        if config.get("ipMasq") and subnet:
            await self._ensure_masq(subnet)
        return {"ips": [{"address": f"{ip}/{prefix}"}]}

    async def _del(self, ifname: str, container_id: str, config: Mapping[str, Any]) -> None:
        # Deleting the host veth end removes the pair (the container end goes with the netns).
        await _run(["ip", "link", "del", _veth_name(container_id, ifname, "h")], check=False)
        ipam = config.get("ipam") or {}
        subnet = ipam.get("subnet")
        if ipam.get("type") != "static" and subnet:
            remaining = await self._ipam.release(subnet, container_id, ifname)
            if remaining == 0 and config.get("ipMasq"):
                await self._del_masq(subnet)

    async def _ensure_bridge(self, bridge: str, mtu: str, gw_cidr: str | None) -> None:
        rc, _, _ = await _run(["ip", "link", "show", bridge], check=False)
        if rc != 0:
            await _run(["ip", "link", "add", bridge, "type", "bridge"])
        await _run(["ip", "link", "set", bridge, "mtu", mtu], check=False)
        await _run(["ip", "link", "set", bridge, "up"])
        if gw_cidr:
            await _run(["ip", "addr", "replace", gw_cidr, "dev", bridge], check=False)

    def _masq_rule(self, subnet: str) -> list[str]:
        # NAT egress leaving the node (do not masquerade intra-subnet delivery).
        return ["POSTROUTING", "-s", subnet, "!", "-d", subnet, "-j", "MASQUERADE"]

    async def _ensure_masq(self, subnet: str) -> None:
        rule = self._masq_rule(subnet)
        rc, _, _ = await _run(["iptables", "-t", "nat", "-C", *rule], check=False)
        if rc != 0:
            await _run(["iptables", "-t", "nat", "-A", *rule], check=False)

    async def _del_masq(self, subnet: str) -> None:
        await _run(["iptables", "-t", "nat", "-D", *self._masq_rule(subnet)], check=False)
