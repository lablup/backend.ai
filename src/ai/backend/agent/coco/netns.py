import asyncio
import hashlib
import ipaddress
import logging
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from ai.backend.common.types import KernelId, SessionId
from ai.backend.logging import BraceStyleAdapter

from .errors import BrokerUnreachableFromNamespace, NetworkSetupFailed

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

RULE_TAG = "bai-coco"


@dataclass(frozen=True)
class NetworkConfig:
    netns_dir: Path
    subnet_pool: ipaddress.IPv4Network
    subnet_prefix: int
    mtu: int
    dns_servers: Sequence[str]
    shim_host: str
    shim_port: int
    upstream_host: str | None
    upstream_port: int | None
    denied_networks: Sequence[ipaddress.IPv4Network]
    reachability_timeout: float


@dataclass(frozen=True)
class SessionNetwork:
    namespace: str
    bridge: str
    host_veth: str
    subnet: ipaddress.IPv4Network
    gateway: ipaddress.IPv4Address
    guest_addr: ipaddress.IPv4Address

    @property
    def netns_path(self) -> Path:
        return Path("/var/run/netns") / self.namespace


def namespace_name(kernel_id: KernelId) -> str:
    return f"bai-{kernel_id.hex[:12]}"


def bridge_name(session_id: SessionId) -> str:
    return f"baibr{session_id.hex[:10]}"


def veth_name(kernel_id: KernelId) -> str:
    return f"baiv{kernel_id.hex[:11]}"


def mac_for_ip(addr: ipaddress.IPv4Address) -> str:
    return "02:42:" + ":".join(f"{octet:02x}" for octet in addr.packed)


class SessionNetworkManager:
    def __init__(self, config: NetworkConfig) -> None:
        self._config = config
        self._lock = asyncio.Lock()
        shim = ipaddress.ip_address(config.shim_host)
        if shim.is_loopback:
            raise NetworkSetupFailed(
                extra_msg=(
                    f"the authorisation shim address {shim} is a loopback address, which no"
                    " session namespace can route to; the address is frozen into the measured"
                    " blob and must be reachable identically from every namespace"
                )
            )
        for denied in config.denied_networks:
            if shim in denied:
                raise NetworkSetupFailed(
                    extra_msg=(
                        f"the authorisation shim address {shim} falls inside the denied network"
                        f" {denied}; every guest would boot, attest, fail to fetch and starve"
                    )
                )
        for server in config.dns_servers:
            if ipaddress.ip_address(server).is_loopback:
                raise NetworkSetupFailed(
                    extra_msg=(
                        f"the resolver {server} is a loopback address, which is unreachable"
                        " from a session namespace and breaks guest image pull"
                    )
                )

    async def _run(self, *args: str, check: bool = True) -> str:
        proc = await asyncio.create_subprocess_exec(
            *args, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()
        if check and proc.returncode != 0:
            raise NetworkSetupFailed(
                extra_msg=f"{' '.join(args)} exited {proc.returncode}: {stderr.decode().strip()}"
            )
        return stdout.decode()

    async def _in_use_subnets(self) -> set[ipaddress.IPv4Network]:
        out = await self._run("ip", "-4", "-o", "addr", "show")
        found: set[ipaddress.IPv4Network] = set()
        for line in out.splitlines():
            fields = line.split()
            if "inet" in fields:
                cidr = fields[fields.index("inet") + 1]
                found.add(ipaddress.IPv4Interface(cidr).network)
        return found

    async def _pick_subnet(self, session_id: SessionId) -> ipaddress.IPv4Network:
        pool = list(self._config.subnet_pool.subnets(new_prefix=self._config.subnet_prefix))
        seed = int.from_bytes(hashlib.sha256(session_id.bytes).digest()[:4], "big")
        taken = await self._in_use_subnets()
        for offset in range(len(pool)):
            candidate = pool[(seed + offset) % len(pool)]
            if candidate not in taken:
                return candidate
        raise NetworkSetupFailed(extra_msg=f"no free subnet in {self._config.subnet_pool}")

    async def _existing_subnet(self, bridge: str) -> ipaddress.IPv4Network | None:
        out = await self._run("ip", "-4", "-o", "addr", "show", "dev", bridge, check=False)
        for line in out.splitlines():
            fields = line.split()
            if "inet" in fields:
                return ipaddress.IPv4Interface(fields[fields.index("inet") + 1]).network
        return None

    def _deny_rules(self, bridge: str) -> list[str]:
        return [
            f"-i {bridge} -d {denied} -j REJECT --reject-with icmp-admin-prohibited"
            for denied in self._config.denied_networks
        ]

    def _forward_rules(self, bridge: str) -> list[str]:
        shim = self._config.shim_host
        return [
            f"-i {bridge} -d {shim}/32 -j ACCEPT",
            f"-o {bridge} -s {shim}/32 -j ACCEPT",
            f"-i {bridge} -o {bridge} -j ACCEPT",
            *self._deny_rules(bridge),
            f"-i {bridge} ! -o {bridge} -j ACCEPT",
            f"-o {bridge} -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT",
            f"-o {bridge} -j DROP",
        ]

    def _input_rules(self, bridge: str) -> list[str]:
        upstream = self._config.upstream_host
        return [
            f"-i {bridge} -d {self._config.shim_host}/32 -j ACCEPT",
            *(
                [
                    f"-i {bridge} -d {upstream}/32 -p tcp"
                    f" --dport {self._config.upstream_port} -j ACCEPT"
                ]
                if upstream is not None
                else []
            ),
            *self._deny_rules(bridge),
        ]

    async def _install_rules(self, bridge: str, subnet: ipaddress.IPv4Network) -> None:
        comment = f"-m comment --comment {RULE_TAG}:{bridge}".split()
        for chain, rules in (
            ("FORWARD", self._forward_rules(bridge)),
            ("INPUT", self._input_rules(bridge)),
        ):
            for position, rule in enumerate(rules, start=1):
                await self._run("iptables", "-I", chain, str(position), *rule.split(), *comment)
        nat = ["iptables", "-t", "nat", "-I"]
        await self._run(
            *nat, *f"POSTROUTING 1 -s {subnet} ! -o {bridge} -j MASQUERADE".split(), *comment
        )
        upstream = self._config.upstream_host
        if upstream is not None:
            await self._run(
                *nat,
                *(
                    f"PREROUTING 1 -i {bridge} -d {self._config.shim_host}/32 -p tcp"
                    f" --dport {self._config.shim_port} -j DNAT"
                    f" --to-destination {upstream}:{self._config.upstream_port}"
                ).split(),
                *comment,
            )
            if ipaddress.ip_address(upstream).is_loopback:
                await self._run("sysctl", "-q", "-w", f"net.ipv4.conf.{bridge}.route_localnet=1")

    async def _remove_rules(self, bridge: str) -> None:
        needle = f'--comment "{RULE_TAG}:{bridge}"'
        for table in ("filter", "nat"):
            listing = await self._run("iptables", "-t", table, "-S", check=False)
            for line in listing.splitlines():
                if needle in line and line.startswith("-A "):
                    args = line[3:].split()
                    chain, spec = args[0], args[1:]
                    await self._run(
                        "iptables", "-t", table, "-D", chain, *_unquote(spec), check=False
                    )

    async def _ensure_bridge(self, bridge: str, session_id: SessionId) -> ipaddress.IPv4Network:
        subnet = await self._existing_subnet(bridge)
        if subnet is not None:
            return subnet
        subnet = await self._pick_subnet(session_id)
        await self._run("ip", "link", "add", bridge, "type", "bridge")
        await self._run("ip", "addr", "add", f"{subnet[1]}/{subnet.prefixlen}", "dev", bridge)
        await self._run("ip", "link", "set", bridge, "up")
        await self._run("sysctl", "-q", "-w", "net.ipv4.ip_forward=1")
        await self._run("sysctl", "-q", "-w", f"net.ipv6.conf.{bridge}.disable_ipv6=1")
        await self._install_rules(bridge, subnet)
        return subnet

    async def create(
        self, kernel_id: KernelId, session_id: SessionId, cluster_idx: int
    ) -> SessionNetwork:
        namespace = namespace_name(kernel_id)
        bridge = bridge_name(session_id)
        veth = veth_name(kernel_id)
        async with self._lock:
            subnet = await self._ensure_bridge(bridge, session_id)
            guest_addr = subnet[2 + max(cluster_idx, 0)]
            network = SessionNetwork(namespace, bridge, veth, subnet, subnet[1], guest_addr)
            await self._run("ip", "netns", "delete", namespace, check=False)
            await self._run("ip", "netns", "add", namespace)
            resolver_dir = self._config.netns_dir / namespace
            resolver_dir.mkdir(parents=True, exist_ok=True)
            (resolver_dir / "resolv.conf").write_text(
                "".join(f"nameserver {server}\n" for server in self._config.dns_servers)
            )
            mtu = str(self._config.mtu)
            await self._run("ip", "link", "delete", veth, check=False)
            for command in (
                f"link add {veth} type veth peer name eth0 netns {namespace}",
                f"link set {veth} master {bridge} up mtu {mtu}",
                f"-n {namespace} link set lo up",
                f"-n {namespace} link set eth0 address {mac_for_ip(guest_addr)} mtu {mtu}",
                f"-n {namespace} addr add {guest_addr}/{subnet.prefixlen} dev eth0",
                f"-n {namespace} link set eth0 up",
                f"-n {namespace} route add default via {subnet[1]}",
            ):
                await self._run("ip", *command.split())
        await self.assert_shim_reachable(network)
        return network

    async def assert_shim_reachable(self, network: SessionNetwork) -> None:
        shim = f"{self._config.shim_host}:{self._config.shim_port}"
        proc = await asyncio.create_subprocess_exec(
            *f"ip netns exec {network.namespace} /bin/bash -c".split(),
            f"exec 3<>/dev/tcp/{self._config.shim_host}/{self._config.shim_port}",
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.PIPE,
        )
        reason = ""
        try:
            async with asyncio.timeout(self._config.reachability_timeout):
                _, stderr = await proc.communicate()
            if proc.returncode != 0:
                reason = stderr.decode().strip() or f"exited {proc.returncode}"
        except TimeoutError:
            proc.kill()
            reason = "timed out"
        if reason:
            raise BrokerUnreachableFromNamespace(
                extra_msg=f"connecting to {shim} from namespace {network.namespace}: {reason}"
            )

    async def destroy(self, kernel_id: KernelId, session_id: SessionId) -> None:
        namespace = namespace_name(kernel_id)
        bridge = bridge_name(session_id)
        async with self._lock:
            await self._run("ip", "netns", "delete", namespace, check=False)
            await self._run("ip", "link", "delete", veth_name(kernel_id), check=False)
            resolver = self._config.netns_dir / namespace
            (resolver / "resolv.conf").unlink(missing_ok=True)
            try:
                resolver.rmdir()
            except OSError:
                pass
            members = await self._run("ip", "-o", "link", "show", "master", bridge, check=False)
            if members.strip():
                return
            await self._remove_rules(bridge)
            await self._run("ip", "link", "delete", bridge, check=False)


def _unquote(spec: Sequence[str]) -> list[str]:
    out: list[str] = []
    pending: list[str] | None = None
    for token in spec:
        if pending is not None:
            pending.append(token)
            if token.endswith('"'):
                joined = " ".join(pending)
                out.append(joined[1:-1])
                pending = None
            continue
        if token.startswith('"') and not token.endswith('"'):
            pending = [token]
            continue
        out.append(token.strip('"'))
    return out
