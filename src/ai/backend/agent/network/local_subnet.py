"""Node-local subnet allocator for per-session LOCAL bridges (BEP-1062).

Every session's LOCAL (control + egress/NAT) bridge sits on a node-local block carved out of a
per-node pool. The index picking that block must be:

- **idempotent per session** — a re-attach of a second kernel must land on the same subnet;
- **collision-free across live sessions on the node** — two sessions sharing a block would put two
  bridges on one subnet, which breaks both the cross-session isolation the separate-bridge design
  relies on (BEP-1062 §8) and the per-subnet MASQ refcount the attach runner keeps; and
- **recoverable across an agent restart** — an allocator that starts empty hands index 0 to the
  next session while a surviving pre-restart session still holds it.

The pool and the per-session block size belong to the operator (`container.local-network-pool` /
`container.local-network-block-size`), because both are site facts we cannot know: the pool must not
collide with the addresses the host already routes, and the block size trades the node's session
ceiling against the addresses one session may hold. The defaults — a /16 pool cut into /26 blocks —
give 1,024 sessions per node with 61 container addresses each, which is a session's kernels on this
node many times over.

The authoritative state is in memory, and the directory under ``state_dir`` is its **journal**, not
a concurrent data structure: ``<state_dir>/<index>`` is a file whose content is the owning
``session_id``, and ``<state_dir>/.layout`` records the pool those indices were cut from. `load`
replays it once at startup; `allocate` decides in memory and writes the record through. This mirrors
dockerd, whose libnetwork allocates from an in-memory bitmap behind a mutex and merely persists the
outcome to boltdb, reading it back only on boot.

**The store is node-wide, and several agents may write it.** What an index names — the bridge
device ``bailo<index>`` and the subnet its gateway sits on — is a node-global name, so the index
space has to be node-global too. A node running one agent per backend (containerd + enroot +
apptainer, the multi-backend layout) therefore has several writers, each owning its own sessions
inside one shared journal.

Anchoring this store per agent instead was tried and is wrong: each agent then starts counting at
index 0, every one of them derives ``bailo0`` and the same gateway subnet, and the second agent's
``setup_session_network`` — which deletes and recreates host devices *by name* — takes the first
agent's bridge away underneath its running session. Measured: a containerd cluster session at 0%
loss went to 100% the moment an apptainer session was created on the same node, with its host-side
veths gone.

Two mechanisms keep the shared journal honest, and neither needs a lock between agents:

- **Owner-tagged claims.** A record is ``<session_id>\n<owner>``, so an agent replaying the journal
  can tell its own sessions (which it may release, and must reconcile against its live containers)
  from another agent's (which it must treat as taken and never touch). A record with no owner line
  predates this and is read as ours, which is what a single-agent node upgrading in place needs.
- **Exclusive create, then move on.** The claim is an ``O_EXCL`` link, so two agents racing for the
  same index cannot both win; the loser simply takes the next free index. That collision is an
  ordinary outcome of a shared pool, not the corruption it used to be reported as.

A node does not upgrade all at once, so the allocator also **adopts** whatever an agent already
holds in its own (pre-node-wide) store: those blocks are carrying live sessions whose bridges are
up on this host, and a node-wide allocator that could not see them would hand the same index to
somebody else. Measured while a co-located agent was still on the old code: the new agent was
handed the block a legacy session already held, and the node ended up with two bridges on
172.30.0.64/26 both claiming .65 as their gateway — the :53 redirect is keyed on that address, so
one session's cluster DNS silently answered for the other and its kernels could not resolve their
peers.

Records are written before the host is mutated. A crash in between leaves a claim with no device,
which restart recovery reconciles against the live containers; the reverse order would leave a
device no record can name.
"""

from __future__ import annotations

import asyncio
import ipaddress
import logging
import socket
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import override

from ai.backend.agent.errors.network import (
    LocalSubnetLayoutChanged,
    LocalSubnetPoolExhausted,
)
from ai.backend.agent.network.journal_io import atomic_exclusive_write, atomic_write
from ai.backend.logging import BraceStyleAdapter

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

# Node-wide on purpose: see the module docstring. This is NOT anchored to an agent's
# var-base-path, because the index it hands out names a node-global bridge device.
_DEFAULT_LOCAL_SUBNET_STATE_DIR = Path("/var/lib/backend.ai/net-local-subnet")
# The shared claim directory is created like /tmp: any co-located agent may add its own claim,
# and the sticky bit stops it removing anyone else's.
_SHARED_DIR_MODE = 0o1777

DEFAULT_LOCAL_POOL = "172.30.0.0/16"
DEFAULT_BLOCK_PREFIXLEN = 26

_LAYOUT_FILE = ".layout"

# One allocator per store, per process. See the module docstring.
_allocators: dict[Path, LocalSubnetAllocator] = {}


@dataclass(frozen=True)
class LocalSubnetLayout:
    """How this node's pool is cut into per-session blocks.

    An index means nothing on its own — it names a block only against a (pool, block size) pair.
    Keeping the two together is what lets the journal notice that the operator re-cut the pool
    under live sessions, instead of quietly reading an old index as a different subnet.
    """

    pool: ipaddress.IPv4Network
    block_prefixlen: int

    @classmethod
    def parse(cls, pool: str, block_prefixlen: int) -> LocalSubnetLayout:
        network = ipaddress.IPv4Network(pool, strict=False)
        if not network.prefixlen <= block_prefixlen <= 30:
            raise ValueError(
                f"the per-session block (/{block_prefixlen}) must be no larger than the pool"
                f" ({network}) and no smaller than /30"
            )
        return cls(pool=network, block_prefixlen=block_prefixlen)

    @property
    def size(self) -> int:
        """How many sessions this node's pool can hold at once."""
        return 1 << (self.block_prefixlen - self.pool.prefixlen)

    @property
    def addresses_per_session(self) -> int:
        """Container addresses in one block: the block minus its network and broadcast addresses,
        minus the one CNI's host-local IPAM spends on the bridge gateway."""
        return (1 << (32 - self.block_prefixlen)) - 3

    def subnet(self, index: int) -> str:
        """The CIDR of block ``index``."""
        if not 0 <= index < self.size:
            raise ValueError(f"local-subnet index {index} is outside the pool ({self})")
        base = int(self.pool.network_address) + (index << (32 - self.block_prefixlen))
        return f"{ipaddress.IPv4Address(base)}/{self.block_prefixlen}"

    def serialize(self) -> str:
        return f"{self.pool} {self.block_prefixlen}"

    @classmethod
    def deserialize(cls, text: str) -> LocalSubnetLayout:
        pool, _, block_prefixlen = text.strip().partition(" ")
        return cls.parse(pool, int(block_prefixlen))

    @override
    def __str__(self) -> str:
        return f"{self.pool} in /{self.block_prefixlen} blocks"


DEFAULT_LAYOUT = LocalSubnetLayout.parse(DEFAULT_LOCAL_POOL, DEFAULT_BLOCK_PREFIXLEN)

# What an unmarked store's indices were cut from: the allocator that wrote it had no pool to
# configure and always meant this one. A store predating the marker is therefore not ambiguous, and
# is held to the same check as any other — it must not be re-read as a pool it was not written from.
_LEGACY_LAYOUT = LocalSubnetLayout.parse("172.30.0.0/16", 24)


def host_ipv4_addresses() -> frozenset[str]:
    """Every IPv4 address currently configured on this host.

    The authority on "is this block already in use here" is the host, not any one journal. An
    agent still running the pre-node-wide code keeps its claims in a store this one cannot see, and
    a leaked bridge is in no store at all — both leave an address sitting on the node, and handing
    that block out again puts two bridges on one subnet with the same gateway.
    """
    found: set[str] = set()
    try:
        import psutil
    except ImportError:  # pragma: no cover - psutil is an agent dependency
        return frozenset()
    try:
        for addrs in psutil.net_if_addrs().values():
            for addr in addrs:
                if addr.family == socket.AF_INET and addr.address:
                    found.add(addr.address)
    except Exception as e:  # pragma: no cover - reading host state must never fail allocation
        log.warning("could not read this host's addresses ({!r}); allocating without them", e)
        return frozenset()
    return frozenset(found)


def get_local_subnet_allocator(
    state_dir: Path | None = None,
    *,
    layout: LocalSubnetLayout | None = None,
    owner: str | None = None,
    legacy_dir: Path | None = None,
    host_addresses: Callable[[], Iterable[str]] | None = None,
) -> LocalSubnetAllocator:
    """The process-wide allocator owning ``state_dir``. Construct the class directly only in
    tests, where each case owns its own store.

    ``owner`` is this agent's id. It is written into every claim so a co-located agent replaying the
    same node-wide journal can tell whose sessions are whose; None means "unowned", which is read
    back as ours (the single-agent node).

    ``legacy_dir`` is this agent's own pre-node-wide store, if it had one. Claims found there are
    adopted at load so a half-upgraded node does not hand out a block a legacy session still holds.

    ``host_addresses`` reads the node's own addresses; defaults to the real reader here and is
    injected only by tests.
    """
    resolved = state_dir if state_dir is not None else _DEFAULT_LOCAL_SUBNET_STATE_DIR
    wanted = layout if layout is not None else DEFAULT_LAYOUT
    if (existing := _allocators.get(resolved)) is not None:
        if existing.layout != wanted:
            # Two collaborators in one process asked for one store under two pools; whichever lost
            # would hand out subnets the other does not believe it owns.
            raise LocalSubnetLayoutChanged(
                f"the node-local subnet store {resolved} is already owned in this process as"
                f" {existing.layout}, but was requested as {wanted}"
            )
        return existing
    allocator = LocalSubnetAllocator(
        resolved,
        layout=wanted,
        owner=owner,
        legacy_dir=legacy_dir,
        host_addresses=host_addresses or host_ipv4_addresses,
    )
    _allocators[resolved] = allocator
    return allocator


class LocalSubnetAllocator:
    """Allocates the session LOCAL bridge's node-local block, journalled to disk."""

    _dir: Path
    _layout: LocalSubnetLayout
    _lock: asyncio.Lock
    #: session_id -> index, for the sessions THIS agent owns.
    _indices: dict[str, int]
    #: Indices a co-located agent holds. Not ours to hand out, and not ours to reconcile away.
    _foreign: set[int]
    _owner: str | None
    #: This agent's pre-node-wide store, whose claims are adopted at load. None when there is none.
    _legacy_dir: Path | None
    #: Reads the host's own addresses, so a block already carried by a device nobody journalled
    #: here (a legacy agent, a leaked bridge) is not handed out a second time.
    _host_addresses: Callable[[], Iterable[str]]
    _loaded: bool

    def __init__(
        self,
        state_dir: Path | None = None,
        *,
        layout: LocalSubnetLayout | None = None,
        owner: str | None = None,
        legacy_dir: Path | None = None,
        host_addresses: Callable[[], Iterable[str]] | None = None,
    ) -> None:
        self._dir = state_dir if state_dir is not None else _DEFAULT_LOCAL_SUBNET_STATE_DIR
        self._layout = layout if layout is not None else DEFAULT_LAYOUT
        self._lock = asyncio.Lock()
        self._indices = {}
        self._foreign = set()
        self._owner = owner
        self._legacy_dir = legacy_dir if legacy_dir != state_dir else None
        # Pure by default: the class is what tests construct, and a reader that inspects the
        # machine would make every one of them depend on whatever bridges it happens to have.
        # `get_local_subnet_allocator` — the production composition root — passes the real one.
        self._host_addresses = host_addresses or (lambda: ())
        self._loaded = False

    @property
    def layout(self) -> LocalSubnetLayout:
        return self._layout

    def subnet(self, index: int) -> str:
        """The CIDR that block ``index`` names under this node's pool."""
        return self._layout.subnet(index)

    def _read_layout(self) -> LocalSubnetLayout | None:
        """The pool the journalled indices were cut from, or None for a store that has never been
        written."""
        try:
            return LocalSubnetLayout.deserialize((self._dir / _LAYOUT_FILE).read_text())
        except (FileNotFoundError, NotADirectoryError):
            return None
        except ValueError as e:
            raise LocalSubnetLayoutChanged(
                f"the node-local subnet store {self._dir} has an unreadable layout marker: {e}"
            ) from e

    def _write_layout(self) -> None:
        if self._read_layout() == self._layout:
            # Already marked, and possibly by another agent — in a sticky shared directory we could
            # not replace their file anyway, and there is nothing to change.
            return
        self._ensure_dir()
        # Atomic overwrite: a crash mid-write must never leave an empty/truncated marker, which
        # _read_layout would reject as an "unreadable layout" and fail block allocation node-wide.
        atomic_write(self._dir / _LAYOUT_FILE, self._layout.serialize())

    def _replay(self) -> dict[str, int]:
        """Rebuild session -> index for OUR sessions, and remember which indices are somebody
        else's.

        A session recorded twice (only possible in a store written by an older, racy allocator)
        keeps its lowest index. A record with no owner line predates owner tagging and is read as
        ours — that is the single-agent node upgrading over its own journal.
        """
        indices: dict[str, int] = {}
        foreign: set[int] = set()
        if not self._dir.is_dir():
            self._foreign = foreign
            return indices
        for entry in sorted(self._dir.iterdir()):
            if not entry.is_file():
                continue
            try:
                index = int(entry.name)  # skips the (dot-prefixed) layout marker
            except ValueError:
                continue
            try:
                session_id, _, owner = entry.read_text().strip().partition("\n")
            except OSError:
                # Another agent's claim we may not even read. It is taken either way.
                foreign.add(index)
                continue
            if owner and owner != self._owner:
                foreign.add(index)
                continue
            indices.setdefault(session_id, index)
        self._foreign = foreign
        return indices

    def _replay_and_reconcile(self) -> dict[str, int]:
        """Replay the journal, and refuse to read it under a pool it was not written from.

        An index is meaningless without the layout that cuts it. Re-reading an old index under a new
        pool would name a subnet the live bridge is not on, so teardown would delete a device that
        belongs to nobody and the next session would be handed a block already in use. Re-cutting
        the pool means draining the node first, and we say so rather than guess.
        """
        indices = self._replay()
        self._adopt_legacy(indices)
        recorded = self._read_layout()
        if recorded is None and indices:
            recorded = _LEGACY_LAYOUT  # an unmarked store with claims predates the marker
        if recorded == self._layout:
            return indices
        if recorded is not None and indices:
            raise LocalSubnetLayoutChanged(
                f"this node's LOCAL subnet pool changed ({recorded} -> {self._layout}) while"
                f" {len(indices)} session(s) still hold blocks cut from the old one"
                f" (store: {self._dir}). Their bridges are on the old subnets, which the new pool"
                " cannot name. Drain this node (or terminate those sessions), or restore the"
                " previous container.local-network-pool / container.local-network-block-size."
            )
        if self._dir.is_dir():
            # No live claims: adopt the configured pool as this store's.
            self._write_layout()
        return indices

    def _blocks_in_use_on_the_host(self) -> set[int]:
        """Indices whose block already holds a live address on this node."""
        pool = self._layout.pool
        block_bits = 32 - self._layout.block_prefixlen
        occupied: set[int] = set()
        for raw in self._host_addresses():
            try:
                addr = ipaddress.IPv4Address(raw)
            except ValueError:
                continue
            if addr not in pool:
                continue
            occupied.add((int(addr) - int(pool.network_address)) >> block_bits)
        return occupied

    def _adopt_legacy(self, indices: dict[str, int]) -> None:
        """Carry this agent's own pre-node-wide claims into the shared journal.

        A node upgrades one agent at a time. The blocks in an agent's old store are carrying live
        sessions whose bridges are already up on this host, so a node-wide allocator that started
        without them would hand the same index to a co-located agent — two bridges on one subnet,
        both answering as its gateway. The index is preserved, never re-picked: it names the device
        that already exists.

        The legacy record is left in place rather than deleted. It costs nothing, adoption is
        idempotent, and an operator who rolls an agent back to the old code still finds its state.
        """
        if self._legacy_dir is None or not self._legacy_dir.is_dir():
            return
        for entry in sorted(self._legacy_dir.iterdir()):
            if not entry.is_file():
                continue
            try:
                index = int(entry.name)
                session_id = entry.read_text().strip().partition("\n")[0]
            except (ValueError, OSError):
                continue
            if not session_id or indices.get(session_id) == index:
                continue
            if index in self._foreign or index in set(indices.values()):
                # Somebody else already holds it node-wide. We cannot move the session — its bridge
                # is up on this index — so say so rather than allocate around a live collision.
                log.error(
                    "local-subnet index {} is held both by this agent's legacy store (session {})"
                    " and by another writer in {}; two bridges now share {}. Drain one of them.",
                    index,
                    session_id,
                    self._dir,
                    self._layout.subnet(index),
                )
                continue
            if self._write_claim(index, session_id):
                log.info(
                    "adopted local-subnet index {} ({}) from the legacy store {}",
                    index,
                    session_id,
                    self._legacy_dir,
                )
            else:
                # It appeared node-wide between our replay and now; treat it as taken either way.
                self._foreign.add(index)
                continue
            indices[session_id] = index

    def _write_claim(self, index: int, session_id: str) -> bool:
        """Claim ``index``. False when a co-located agent got there first.

        Not an error: the journal is node-wide (see the module docstring), so losing a race for one
        index just means taking the next. Raising here is what the per-agent store was introduced
        to avoid, and that cure was worse than the disease — it gave every agent its own index
        space and let them collide on the bridge names those indices produce.
        """
        self._ensure_dir()
        self._write_layout()  # the first claim is what marks a fresh store
        record = f"{session_id}\n{self._owner}" if self._owner else session_id
        try:
            # Atomic + exclusive: a crash mid-write must never leave an empty claim (replay would
            # read a block owned by "" -- a leaked /26), and O_EXCL is what makes the race between
            # two agents resolvable without a lock.
            atomic_exclusive_write(self._dir / str(index), record)
        except FileExistsError:
            return False
        return True

    def _ensure_dir(self) -> None:
        """The shared claim directory, created so any co-located agent may add to it.

        Sticky + world-writable, exactly like /tmp: an agent running as its own uid can create its
        claims, and cannot unlink another agent's. Best-effort — a directory somebody else created
        is not ours to re-mode, and the claim below will say plainly if we cannot write.
        """
        self._dir.mkdir(parents=True, exist_ok=True)
        try:
            if (self._dir.stat().st_mode & 0o7777) != _SHARED_DIR_MODE:
                self._dir.chmod(_SHARED_DIR_MODE)
        except OSError:
            pass

    async def _load_locked(self) -> None:
        if self._loaded:
            return
        self._indices = await asyncio.to_thread(self._replay_and_reconcile)
        self._loaded = True

    async def load(self) -> None:
        """Replay the journal into memory. Idempotent; called lazily on first use, and callable
        explicitly from the agent's startup path."""
        async with self._lock:
            await self._load_locked()

    async def allocate(self, session_id: str) -> int:
        """Claim (or re-read) this session's node-local block index."""
        async with self._lock:
            await self._load_locked()
            if (existing := self._indices.get(session_id)) is not None:
                return existing  # idempotent re-allocate
            used = set(self._indices.values()) | self._foreign
            # The host is the last word on which blocks are already carrying traffic. A co-located
            # agent still on the pre-node-wide code journals nowhere we can read, and a bridge
            # leaked by a teardown that did not finish is journalled nowhere at all — both leave an
            # address on this node, and reusing that block puts two bridges on one subnet, both
            # answering as its gateway. Measured: the cluster-DNS :53 redirect is keyed on that
            # gateway address, so one session's resolver silently answered for the other and its
            # kernels could not resolve their peers.
            occupied = await asyncio.to_thread(self._blocks_in_use_on_the_host)
            for index in range(self._layout.size):
                if index in used:
                    continue
                if index in occupied:
                    log.warning(
                        "local-subnet index {} ({}) is already carried by a device on this host"
                        " that no journal here names; skipping it",
                        index,
                        self._layout.subnet(index),
                    )
                    self._foreign.add(index)
                    continue
                # Journal before the caller mutates the host, and only then commit to memory.
                if not await asyncio.to_thread(self._write_claim, index, session_id):
                    # A co-located agent claimed it between our replay and now. Remember that and
                    # take the next one rather than handing out a block we do not own.
                    self._foreign.add(index)
                    continue
                self._indices[session_id] = index
                return index
            raise LocalSubnetPoolExhausted(
                f"every one of this node's {self._layout.size} LOCAL subnet blocks is held by a"
                f" live session ({self._layout}). Cut the pool into more, smaller blocks by raising"
                f" container.local-network-block-size to /{self._layout.block_prefixlen + 1}"
                f" ({self._layout.size * 2} sessions per node,"
                f" {(self._layout.addresses_per_session - 1) // 2} container addresses each), or"
                " widen container.local-network-pool. Both are re-cut on a drained node only."
            )

    async def allocate_subnet(self, session_id: str) -> str:
        """The CIDR of this session's block, claiming one if it holds none."""
        return self._layout.subnet(await self.allocate(session_id))

    async def subnet_of(self, session_id: str) -> str | None:
        """The CIDR of this session's block, or None if it holds none. Never allocates — a teardown
        asking which subnet to clean up must not mint a fresh one."""
        index = await self.lookup(session_id)
        return self._layout.subnet(index) if index is not None else None

    async def sessions(self) -> frozenset[str]:
        """Every session the journal still names. Restart recovery diffs this against the live
        containers to reclaim blocks whose session died while the agent was down — without it a
        durable journal only ever grows, and the pool is finite."""
        async with self._lock:
            await self._load_locked()
            return frozenset(self._indices)

    async def lookup(self, session_id: str) -> int | None:
        """This session's index, or None if it holds none. Never allocates — a teardown must
        not mint a fresh index and then delete the bridge that index names."""
        async with self._lock:
            await self._load_locked()
            return self._indices.get(session_id)

    async def release(self, session_id: str) -> None:
        async with self._lock:
            await self._load_locked()
            index = self._indices.get(session_id)
            if index is None:
                return
            # Drop the record first: a failed unlink must not leave memory handing the index out
            # again while the journal still names this session.
            await asyncio.to_thread((self._dir / str(index)).unlink, True)
            if self._legacy_dir is not None:
                # Adoption left it behind on purpose; releasing the block is when it stops being
                # true, and a legacy store nobody prunes only ever grows.
                await asyncio.to_thread((self._legacy_dir / str(index)).unlink, True)
            del self._indices[session_id]


def cluster_host_ips(subnet: str, hostnames: Sequence[str]) -> dict[str, str]:
    """Lay peer hostnames out at deterministic addresses in a session's LOCAL subnet.

    Single-node cluster sessions have no manager-assigned overlay IPs (those are the multi-node
    path), and containerd has no built-in cluster DNS, so peers can only find each other if every
    kernel writes the same ``hostname -> IP`` map into /etc/hosts. The map has to be computable by
    each kernel independently, before any of them has attached — so it is a pure function of the
    (session-wide, identical for every kernel) ordered hostname list and the session's subnet.

    Address ``i`` is the ``i``-th usable host after the gateway (``.1``); the caller pins each
    kernel's own attachment at its address so the mapping is real, not just advertised. Raises if
    the subnet cannot hold every peer — a caller must size the LOCAL block for the cluster.
    """
    hosts = iter(ipaddress.IPv4Network(subnet).hosts())
    next(hosts)  # the first usable address is the bridge gateway (isGateway/isDefaultGateway)
    mapping: dict[str, str] = {}
    for hostname in hostnames:
        try:
            mapping[hostname] = str(next(hosts))
        except StopIteration:
            raise LocalSubnetPoolExhausted(
                f"the LOCAL subnet {subnet} cannot hold {len(hostnames)} cluster peers; raise"
                " container.local-network-block-size (a larger per-session block)"
            ) from None
    return mapping
