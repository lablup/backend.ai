"""Native veth/bridge attach runner (BEP-1062) — replaces the CNI ``bridge`` plugin binary.

The BEP-1062 data plane is host-native: the session fabric (vxlan device, bridge, FDB/ARP)
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
import contextlib
import hashlib
import ipaddress
import logging
import re
import shutil
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from ai.backend.agent.errors.network import (
    NetworkStateStoreConflict,
    StaticAddressUnavailable,
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
        self,
        subnet: str,
        container_id: str,
        ifname: str,
        *,
        reserve: Sequence[str],
        requested: str | None = None,
    ) -> str:
        """Claim an address in ``subnet`` for this owner, journalled.

        ``requested`` pins a specific address instead of taking the next free one — how a
        single-node cluster kernel lands on the deterministic IP its peers wrote into /etc/hosts.
        It must be a usable host address of the subnet and not already held by a different owner;
        the gateway is in ``reserve`` so it can never be requested. A pin that cannot be honoured
        raises rather than falling back to a free address: the peers' /etc/hosts already names the
        pinned address, so a kernel that quietly took a different one would be unreachable under
        the name its peers use — a failed kernel is the better outcome."""
        owner = f"{container_id}/{ifname}"
        async with self._lock:
            d = self._subnet_dir(subnet)
            owners = await self._owners_of(d)
            if (existing := owners.get(owner)) is not None:
                # Idempotent re-ADD — but only if it lands where the caller asked. An owner already
                # holding a *different* address (a re-attach whose DEL never landed; container_id is
                # the kernel id, stable across a restart) must not silently keep it.
                if requested is not None and existing != requested:
                    raise StaticAddressUnavailable(
                        f"{owner} already holds {existing} in {subnet}, but must be pinned at"
                        f" {requested}; release the stale claim before re-attaching"
                    )
                return existing
            used = set(owners.values()) | set(reserve)
            if requested is not None:
                # Membership in the network is not enough: it also admits the network and broadcast
                # addresses, which the dynamic path below (hosts()) excludes.
                net = ipaddress.ip_network(subnet)
                addr = ipaddress.ip_address(requested)
                if addr not in net or addr in (net.network_address, net.broadcast_address):
                    raise StaticAddressUnavailable(
                        f"requested address {requested} is not a usable host address of {subnet}"
                    )
                if requested in used:
                    raise StaticAddressUnavailable(
                        f"requested address {requested} in {subnet} is already taken"
                    )
                await asyncio.to_thread(self._write_claim, d, requested, owner)
                owners[owner] = requested
                return requested
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

    async def purge_subnet(self, subnet: str) -> None:
        """Drop every record for a subnet whose block is about to be given back.

        Per-container releases can be lost — a detach that failed, a container whose attachment
        record did not survive — and a leftover claim used to be harmless: the next session to take
        the block simply picked another free address. It is not harmless now that a single-node
        cluster *pins* its kernels, since a stale claim on the address a peer is pinned at fails
        that kernel outright, and would keep failing until the agent restarts. The block is only
        reclaimed once the session's containers are gone, so nothing can still own these records.
        """
        async with self._lock:
            d = self._subnet_dir(subnet)
            await asyncio.to_thread(shutil.rmtree, d, True)
            self._owners.pop(d, None)

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
        ip = await self._ipam.allocate(
            subnet, container_id, ifname, reserve=[gateway], requested=ipam.get("requested_ip")
        )
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
        if not await self._is_wired(host_veth, netns, ifname):
            # The host end existing is NOT proof the container is wired: a half-finished attach
            # (the task died mid-ADD, so the peer never made it into the netns) leaves it behind,
            # and taking that as "already attached" would return success for a container that comes
            # up with no interface at all — its REPL never binds and its published ports DNAT to an
            # address nothing owns. Clear the leftover and wire it properly.
            await _run(["ip", "link", "del", host_veth], check=False)
            try:
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
                    await _run(
                        ns + ["ip", "route", "replace", "default", "via", gateway], check=False
                    )
            except Exception:
                # Undo our own half-attach. Nothing else will: the caller's rollback covers the
                # attachments that SUCCEEDED, not the one that raised, and a veth pair whose peer
                # never reached a netns is reaped by nothing — it sits in the host namespace, with
                # its address still claimed, until someone notices. The container-side end goes with
                # the host end, and the address claim is this owner's to give back.
                await _run(["ip", "link", "del", host_veth], check=False)
                if ipam.get("type") != "static" and subnet:
                    with contextlib.suppress(Exception):
                        await self._ipam.release(subnet, container_id, ifname)
                raise

        if config.get("ipMasq") and subnet:
            await self._ensure_masq(subnet)
            await self._ensure_forward_accept(bridge)
        return {"ips": [{"address": f"{ip}/{prefix}"}]}

    async def _is_wired(self, host_veth: str, netns: str, ifname: str) -> bool:
        """Is this container already attached — really attached, both ends?

        Both halves are checked because an idempotent re-ADD (a retry, a restart) must be a no-op
        while a half-finished one must be rebuilt, and only the container side tells them apart.
        """
        rc, _, _ = await _run(["ip", "link", "show", host_veth], check=False)
        if rc != 0:
            return False
        rc, _, _ = await _run(
            ["nsenter", "--net=" + netns, "--", "ip", "link", "show", ifname], check=False
        )
        return rc == 0

    async def _del(self, ifname: str, container_id: str, config: Mapping[str, Any]) -> None:
        # Deleting the host veth end removes the pair (the container end goes with the netns).
        await _run(["ip", "link", "del", _veth_name(container_id, ifname, "h")], check=False)
        ipam = config.get("ipam") or {}
        subnet = ipam.get("subnet")
        if ipam.get("type") != "static" and subnet:
            remaining = await self._ipam.release(subnet, container_id, ifname)
            if remaining == 0 and config.get("ipMasq"):
                await self._del_masq(subnet)
                await self._del_forward_accept(str(config["bridge"]))

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

    def _forward_accept_rules(self, bridge: str) -> list[list[str]]:
        # br_netfilter + a DROP FORWARD policy (a node co-hosting Docker or kube-proxy, or a
        # hardened host) routes bridged frames through iptables FORWARD, so egress leaving the
        # LOCAL bridge -- and same-node container<->container over it -- is dropped and the bridge
        # goes silently dead. Accept traffic in and out of this bridge, as Docker does for its own.
        # Paired with the NAT MASQUERADE above and torn down on the same last-owner path.
        return [
            ["FORWARD", "-i", bridge, "-j", "ACCEPT"],
            ["FORWARD", "-o", bridge, "-j", "ACCEPT"],
        ]

    async def _ensure_forward_accept(self, bridge: str) -> None:
        for rule in self._forward_accept_rules(bridge):
            rc, _, _ = await _run(["iptables", "-C", *rule], check=False)
            if rc != 0:
                await _run(["iptables", "-I", *rule], check=False)

    async def _del_forward_accept(self, bridge: str) -> None:
        for rule in self._forward_accept_rules(bridge):
            await _run(["iptables", "-D", *rule], check=False)
