"""Kernel- and filesystem-level state the network backend creates on one node.

Everything here is scoped by the ``bai`` device-name prefix and the ``bai:`` iptables comment the
backend stamps on its own rules — the same markers the production cleanup paths key off. That is
deliberate: if a collector found leaks by some *other* rule than the one teardown uses, it would
report resources teardown was never meant to own, and the suite would train people to ignore it.
"""

from __future__ import annotations

import ipaddress
import json
import shlex
from collections.abc import Awaitable, Callable, Sequence

from ai.backend.testutils.dataplane.collectors.base import Resource
from ai.backend.testutils.dataplane.nodes import CommandFailed, Node

# `baibr{vni}` (overlay bridge), `baivx{vni}` (vxlan device), `bailo{vni}` (per-session LOCAL
# bridge), and the `bai<hex>` host-side veths the attach runner names.
DEFAULT_DEVICE_PREFIXES: tuple[str, ...] = ("bai",)

# `-m comment --comment bai:<container_id>`, the tag published port-forwards carry.
IPTABLES_COMMENT_MARKER = "bai:"

DEFAULT_IPTABLES_TABLES: tuple[str, ...] = ("filter", "nat")


class NetworkLinkCollector:
    """Netlink devices belonging to the backend, on one node.

    A container's host-side veth is caught two ways — by its own ``bai`` name and by its master
    being one of our bridges — because a half-finished attach can leave a veth whose name the
    runner never got to set.
    """

    _node: Node
    _prefixes: tuple[str, ...]

    def __init__(self, node: Node, *, prefixes: Sequence[str] = DEFAULT_DEVICE_PREFIXES) -> None:
        self._node = node
        self._prefixes = tuple(prefixes)

    @property
    def kind(self) -> str:
        return "link"

    def _is_ours(self, ifname: str) -> bool:
        return any(ifname.startswith(prefix) for prefix in self._prefixes)

    def parse(self, raw: str) -> set[Resource]:
        try:
            links = json.loads(raw)
        except json.JSONDecodeError as e:
            raise CommandFailed(
                f"[{self._node.name}] `ip -json link` did not return JSON; "
                "an iproute2 too old for -json cannot be used by this harness"
            ) from e
        found: set[Resource] = set()
        for link in links:
            ifname = link.get("ifname", "")
            master = link.get("master", "")
            if not (self._is_ours(ifname) or self._is_ours(master)):
                continue
            detail = f"{link.get('link_type', '?')} mtu={link.get('mtu')} "
            detail += f"state={link.get('operstate')}"
            if master:
                detail += f" master={master}"
            found.add(Resource(self.kind, self._node.name, ifname, detail))
        return found

    async def collect(self) -> set[Resource]:
        # NOT `-details`. iproute2 (through at least 6.1.0) prints a VXLAN device's fan-map as raw
        # text *inside* the JSON object — `"id":4098fan-map 83.114.0.0/14615:...` — so
        # `ip -details -json link show` is unparseable on any host that has a vxlan device, which
        # is every host this suite targets. Without `-details` there is no `linkinfo`, hence the
        # coarser `link_type` in the detail above; identity does not depend on it.
        result = await self._node.run(["ip", "-json", "link", "show"])
        return self.parse(result.stdout)


class IptablesRuleCollector:
    """Rules the backend installed, on one node.

    Chain *declarations* are collected alongside rules: a leaked empty ``CNI-<hash>`` chain is
    invisible in the rule list but still accumulates, and enough of them make an iptables restore
    slow enough to notice.
    """

    _node: Node
    _tables: tuple[str, ...]
    _prefixes: tuple[str, ...]

    def __init__(
        self,
        node: Node,
        *,
        tables: Sequence[str] = DEFAULT_IPTABLES_TABLES,
        prefixes: Sequence[str] = DEFAULT_DEVICE_PREFIXES,
    ) -> None:
        self._node = node
        self._tables = tuple(tables)
        self._prefixes = tuple(prefixes)

    @property
    def kind(self) -> str:
        return "iptables"

    def _mentions_ours(self, line: str) -> bool:
        if IPTABLES_COMMENT_MARKER in line:
            return True
        if "CNI-" in line:
            return True
        tokens = shlex.split(line)
        return any(token.startswith(prefix) for token in tokens for prefix in self._prefixes)

    def parse(self, table: str, raw: str) -> set[Resource]:
        found: set[Resource] = set()
        for line in raw.splitlines():
            line = line.strip()
            if line.startswith(":"):
                # `:CNI-abc - [0:0]` — drop the packet counters, which change every poll.
                chain = line[1:].split()[0]
                if not chain.startswith("CNI-"):
                    continue
                found.add(Resource(self.kind, self._node.name, f"{table} chain {chain}"))
                continue
            if not line.startswith("-A "):
                continue
            if not self._mentions_ours(line):
                continue
            found.add(Resource(self.kind, self._node.name, f"{table} {line}", table))
        return found

    async def collect(self) -> set[Resource]:
        found: set[Resource] = set()
        for table in self._tables:
            result = await self._node.run(["iptables-save", "-t", table])
            found |= self.parse(table, result.stdout)
        return found


class StateFileCollector:
    """Records in the durable allocator journals: `net-local-subnet/<index>` (content: session id)
    and `net-ipam/<subnet>/<ip>` (content: `<container_id>/<ifname>`).

    The content is read into the ident, not the detail: two different sessions holding block 3 at
    two different times are two different leaks, and collapsing them onto the path alone would
    hide a hand-off bug behind a stable file name.
    """

    _node: Node
    _dirs: tuple[str, ...]

    def __init__(self, node: Node, *, dirs: Sequence[str]) -> None:
        self._node = node
        self._dirs = tuple(dirs)

    @property
    def kind(self) -> str:
        return "state-file"

    def parse(self, raw: str) -> set[Resource]:
        found: set[Resource] = set()
        for line in raw.splitlines():
            if not line.strip():
                continue
            path, _, content = line.partition("\t")
            found.add(Resource(self.kind, self._node.name, f"{path}={content}"))
        return found

    async def collect(self) -> set[Resource]:
        # `-print0`-free on purpose: these paths are allocator-generated (indices, subnets, IPs)
        # and cannot contain whitespace, and a plain loop works identically over ssh.
        script = (
            "for d in " + " ".join(shlex.quote(d) for d in self._dirs) + "; do "
            '[ -d "$d" ] || continue; '
            'find "$d" -type f ! -name .layout | while read -r f; do '
            'printf "%s\\t%s\\n" "$f" "$(tr -d "\\n" < "$f")"; '
            "done; done"
        )
        result = await self._node.run(["sh", "-c", script])
        return self.parse(result.stdout)


class MountCollector:
    """Mounts under the scratch root — the tmpfs MEMORY scratches and bind mounts a kernel gets.

    An unmounted-but-forgotten tmpfs holds its pages until reboot, so this leaks memory rather
    than just clutter.
    """

    _node: Node
    _prefixes: tuple[str, ...]

    def __init__(self, node: Node, *, prefixes: Sequence[str]) -> None:
        self._node = node
        self._prefixes = tuple(prefixes)

    @property
    def kind(self) -> str:
        return "mount"

    def parse(self, raw: str) -> set[Resource]:
        found: set[Resource] = set()
        for line in raw.splitlines():
            target, _, fstype = line.partition(" ")
            if not target:
                continue
            if not any(target.startswith(prefix) for prefix in self._prefixes):
                continue
            found.add(Resource(self.kind, self._node.name, target, fstype))
        return found

    async def collect(self) -> set[Resource]:
        result = await self._node.run(["findmnt", "-rno", "TARGET,FSTYPE"])
        return self.parse(result.stdout)


class ScratchDirCollector:
    """Per-kernel scratch directories that no container record claims.

    `MountCollector` cannot see these: a scratch is bind-mounted only while its container exists,
    so once the container is gone the directory is left behind *unmounted* and `findmnt` reports
    nothing. It still holds the kernel's work data and its disk. A TERMINATED kernel whose scratch
    survived by twelve days is what prompted this collector.

    Ownership is decided the same way `DockerSandboxCollector` decides it — by asking the runtime
    what it still has a record of, rather than by guessing from the name. `live_ids` is a callable,
    not a set, because a snapshot is taken repeatedly and a set captured at construction would go
    stale between polls.
    """

    _node: Node
    _roots: tuple[str, ...]
    _live_ids: Callable[[], Awaitable[set[str]]]

    def __init__(
        self,
        node: Node,
        *,
        roots: Sequence[str],
        live_ids: Callable[[], Awaitable[set[str]]],
    ) -> None:
        self._node = node
        self._roots = tuple(roots)
        self._live_ids = live_ids

    @property
    def kind(self) -> str:
        return "scratch-dir"

    def parse(self, raw: str, live: set[str]) -> set[Resource]:
        found: set[Resource] = set()
        for path in raw.split():
            path = path.strip()
            if not path:
                continue
            if path.rsplit("/", 1)[-1] in live:
                continue
            found.add(Resource(self.kind, self._node.name, path))
        return found

    async def collect(self) -> set[Resource]:
        # A root that does not exist is a misconfiguration, not an empty result. Reporting "no
        # scratch leaked" because the harness was pointed at the wrong directory is exactly the
        # false negative this suite must never produce -- and the default (`/var/lib/backend.ai`)
        # does not match a dev setup, whose agent uses a repo-relative `scratch-root`.
        existing = " ".join(shlex.quote(r) for r in self._roots)
        # `if/fi`, not `[ -d ] && ...`: with `&&` the loop's exit status is the last test's, so a
        # missing root would surface as a shell failure instead of the diagnosable message below.
        probe = await self._node.run([
            "sh",
            "-c",
            f'for d in {existing}; do if [ -d "$d" ]; then printf "%s\\n" "$d"; fi; done',
        ])
        if not probe.lines:
            raise CommandFailed(
                f"[{self._node.name}] none of the configured scratch roots exist: "
                f"{list(self._roots)} -- set BAI_DATAPLANE_SCRATCH_ROOTS to the agent's "
                "`scratch-root`, or this collector silently reports every host as clean"
            )
        script = (
            "for d in " + " ".join(shlex.quote(r) for r in probe.lines) + "; do "
            'find "$d" -mindepth 1 -maxdepth 1 -type d; done'
        )
        listing = await self._node.run(["sh", "-c", script])
        return self.parse(listing.stdout, await self._live_ids())


class NeighbourCollector:
    """FDB and ARP entries the coordinator programs onto the overlay bridge.

    These are the entries a peer's `reconcile_endpoints` adds and removes. A stale one points a
    departed container's MAC at a VTEP that no longer serves it — traffic for a *reused* address
    then goes to the wrong node, which is a correctness failure, not just clutter.
    """

    _node: Node
    _prefixes: tuple[str, ...]

    def __init__(self, node: Node, *, prefixes: Sequence[str] = DEFAULT_DEVICE_PREFIXES) -> None:
        self._node = node
        self._prefixes = tuple(prefixes)

    @property
    def kind(self) -> str:
        return "neigh"

    def _is_ours(self, dev: str) -> bool:
        return any(dev.startswith(prefix) for prefix in self._prefixes)

    def parse_fdb(self, raw: str) -> set[Resource]:
        found: set[Resource] = set()
        for line in raw.splitlines():
            tokens = line.split()
            if not tokens:
                continue
            dev = _value_after(tokens, "dev")
            if dev is None or not self._is_ours(dev):
                continue
            dst = _value_after(tokens, "dst")
            found.add(
                Resource(self.kind, self._node.name, f"fdb {tokens[0]} dev {dev}", f"dst={dst}")
            )
        return found

    def parse_neigh(self, raw: str) -> set[Resource]:
        found: set[Resource] = set()
        for line in raw.splitlines():
            tokens = line.split()
            if not tokens:
                continue
            dev = _value_after(tokens, "dev")
            if dev is None or not self._is_ours(dev):
                continue
            found.add(
                Resource(
                    self.kind,
                    self._node.name,
                    f"neigh {tokens[0]} dev {dev}",
                    _value_after(tokens, "lladdr") or "",
                )
            )
        return found

    async def collect(self) -> set[Resource]:
        fdb = await self._node.run(["bridge", "fdb", "show"])
        neigh = await self._node.run(["ip", "neigh", "show"])
        return self.parse_fdb(fdb.stdout) | self.parse_neigh(neigh.stdout)


def _value_after(tokens: Sequence[str], key: str) -> str | None:
    for i, token in enumerate(tokens):
        if token == key and i + 1 < len(tokens):
            return tokens[i + 1]
    return None


def ip_in_pool(ip: str, pool: str) -> bool:
    """Whether an address falls in a configured pool — used by scenario assertions that need to
    tell a session's overlay address from an unrelated one."""
    try:
        return ipaddress.ip_address(ip) in ipaddress.ip_network(pool, strict=False)
    except ValueError:
        return False
