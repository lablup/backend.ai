"""Node-local /24 allocator for per-session LOCAL bridges (BEP-1062).

Every session's LOCAL (control + egress/NAT) bridge sits on a node-local /24 carved out of a
per-node pool. The index picking that /24 must be:

- **idempotent per session** — a re-attach of a second kernel must land on the same subnet;
- **collision-free across live sessions on the node** — two sessions sharing a /24 would put two
  bridges on one subnet, which breaks both the cross-session isolation the separate-bridge design
  relies on (BEP-1062 §8) and the per-subnet MASQ refcount the attach runner keeps; and
- **recoverable across an agent restart** — an allocator that starts empty hands index 0 to the
  next session while a surviving pre-restart session still holds it.

The authoritative state is therefore in memory, and the directory under ``state_dir`` is its
**journal**, not a concurrent data structure: ``<state_dir>/<index>`` is a file whose content is
the owning ``session_id``. `load` replays it once at startup; `allocate` decides in memory and
writes the record through. This mirrors dockerd, whose libnetwork allocates from an in-memory
bitmap behind a mutex and merely persists the outcome to boltdb, reading it back only on boot.

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
from pathlib import Path

from ai.backend.agent.errors.network import LocalSubnetPoolExhausted, NetworkStateStoreConflict

_DEFAULT_LOCAL_SUBNET_STATE_DIR = Path("/var/lib/backend.ai/net-local-subnet")
_DEFAULT_POOL_SIZE = 256

# One allocator per store, per process. See the module docstring.
_allocators: dict[Path, LocalSubnetAllocator] = {}


def get_local_subnet_allocator(state_dir: Path | None = None) -> LocalSubnetAllocator:
    """The process-wide allocator owning ``state_dir``. Construct the class directly only in
    tests, where each case owns its own store."""
    resolved = state_dir if state_dir is not None else _DEFAULT_LOCAL_SUBNET_STATE_DIR
    if (existing := _allocators.get(resolved)) is not None:
        return existing
    allocator = LocalSubnetAllocator(resolved)
    _allocators[resolved] = allocator
    return allocator


class LocalSubnetAllocator:
    """Allocates the session LOCAL bridge's node-local /24 index, journalled to disk."""

    _dir: Path
    _lock: asyncio.Lock
    _pool_size: int
    _indices: dict[str, int]
    _loaded: bool

    def __init__(
        self,
        state_dir: Path | None = None,
        *,
        pool_size: int = _DEFAULT_POOL_SIZE,
    ) -> None:
        self._dir = state_dir if state_dir is not None else _DEFAULT_LOCAL_SUBNET_STATE_DIR
        self._lock = asyncio.Lock()
        self._pool_size = pool_size
        self._indices = {}
        self._loaded = False

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
                index = int(entry.name)
            except ValueError:
                continue
            session_id = entry.read_text().strip()
            indices.setdefault(session_id, index)
        return indices

    def _write_claim(self, index: int, session_id: str) -> None:
        self._dir.mkdir(parents=True, exist_ok=True)
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
        self._indices = await asyncio.to_thread(self._replay)
        self._loaded = True

    async def load(self) -> None:
        """Replay the journal into memory. Idempotent; called lazily on first use, and callable
        explicitly from the agent's startup path."""
        async with self._lock:
            await self._load_locked()

    async def allocate(self, session_id: str) -> int:
        """Claim (or re-read) this session's node-local /24 index."""
        async with self._lock:
            await self._load_locked()
            if (existing := self._indices.get(session_id)) is not None:
                return existing  # idempotent re-allocate
            used = set(self._indices.values())
            for index in range(self._pool_size):
                if index in used:
                    continue
                # Journal before the caller mutates the host, and only then commit to memory.
                await asyncio.to_thread(self._write_claim, index, session_id)
                self._indices[session_id] = index
                return index
            raise LocalSubnetPoolExhausted(
                f"node-local LOCAL subnet pool exhausted (>{self._pool_size} sessions/node)"
            )

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
