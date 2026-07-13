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

That works because a store has exactly one writer on the node — the agent, or (when privilege is
separated) the network helper, never both — and exactly one owner per process, obtained via
`get_local_subnet_allocator`. Nothing here defends against a second writer, and nothing should:
`setup_session_network` already deletes and recreates host devices by name, so a second writer
destroys the data plane long before it could corrupt this journal. A record that exists on disk
while the owner believes it free means exactly that has happened, so the claim raises
`NetworkStateStoreConflict` instead of quietly allocating around it.

Records are written before the host is mutated. A crash in between leaves a claim with no device,
which restart recovery reconciles against the live containers; the reverse order would leave a
device no record can name.
"""

from __future__ import annotations

import asyncio
import ipaddress
from dataclasses import dataclass
from pathlib import Path
from typing import override

from ai.backend.agent.errors.network import (
    LocalSubnetLayoutChanged,
    LocalSubnetPoolExhausted,
    NetworkStateStoreConflict,
)

_DEFAULT_LOCAL_SUBNET_STATE_DIR = Path("/var/lib/backend.ai/net-local-subnet")

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


def get_local_subnet_allocator(
    state_dir: Path | None = None,
    *,
    layout: LocalSubnetLayout | None = None,
) -> LocalSubnetAllocator:
    """The process-wide allocator owning ``state_dir``. Construct the class directly only in
    tests, where each case owns its own store."""
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
    allocator = LocalSubnetAllocator(resolved, layout=wanted)
    _allocators[resolved] = allocator
    return allocator


class LocalSubnetAllocator:
    """Allocates the session LOCAL bridge's node-local block, journalled to disk."""

    _dir: Path
    _layout: LocalSubnetLayout
    _lock: asyncio.Lock
    _indices: dict[str, int]
    _loaded: bool

    def __init__(
        self,
        state_dir: Path | None = None,
        *,
        layout: LocalSubnetLayout | None = None,
    ) -> None:
        self._dir = state_dir if state_dir is not None else _DEFAULT_LOCAL_SUBNET_STATE_DIR
        self._layout = layout if layout is not None else DEFAULT_LAYOUT
        self._lock = asyncio.Lock()
        self._indices = {}
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
        self._dir.mkdir(parents=True, exist_ok=True)
        (self._dir / _LAYOUT_FILE).write_text(self._layout.serialize())

    def _replay(self) -> dict[str, int]:
        """Rebuild session -> index from the journal. A session recorded twice (only possible in a
        store written by an older, racy allocator) keeps its lowest index."""
        indices: dict[str, int] = {}
        if not self._dir.is_dir():
            return indices
        for entry in sorted(self._dir.iterdir()):
            if not entry.is_file():
                continue
            try:
                index = int(entry.name)  # skips the (dot-prefixed) layout marker
            except ValueError:
                continue
            session_id = entry.read_text().strip()
            indices.setdefault(session_id, index)
        return indices

    def _replay_and_reconcile(self) -> dict[str, int]:
        """Replay the journal, and refuse to read it under a pool it was not written from.

        An index is meaningless without the layout that cuts it. Re-reading an old index under a new
        pool would name a subnet the live bridge is not on, so teardown would delete a device that
        belongs to nobody and the next session would be handed a block already in use. Re-cutting
        the pool means draining the node first, and we say so rather than guess.
        """
        indices = self._replay()
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

    def _write_claim(self, index: int, session_id: str) -> None:
        self._dir.mkdir(parents=True, exist_ok=True)
        self._write_layout()  # the first claim is what marks a fresh store
        try:
            with (self._dir / str(index)).open("x") as f:
                f.write(session_id)
        except FileExistsError as e:
            raise NetworkStateStoreConflict(
                f"local-subnet index {index} exists on disk but is free in memory "
                f"(store: {self._dir}) — another writer owns this node's network"
            ) from e

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
            used = set(self._indices.values())
            for index in range(self._layout.size):
                if index in used:
                    continue
                # Journal before the caller mutates the host, and only then commit to memory.
                await asyncio.to_thread(self._write_claim, index, session_id)
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
            del self._indices[session_id]
