"""Who on this NODE is using a given ESP pair, durably and across processes.

An SA and its policy belong to a (self VTEP, peer VTEP, underlay port) triple, and every session
between those two nodes on that port shares them. The refcount deciding when they may be removed
therefore has to be node-wide -- but it lived in one process's memory, which is only node-wide in
the deployment where a single privnet owns the host's networking. Where each agent runs the
backend in-process instead, two agents on one host each believed they were the pair's only user,
and the first session to end took the other's protection with it: the egress guard turns that into
a dead tunnel rather than a clear-text one, but dead until the next reconcile is still an outage
nobody asked for.

This is the same shape (and the same directory conventions) as the node-local subnet journal next
door, which exists because the identical assumption was wrong there and was measured going from
0% to 100% loss on a multi-backend node.
"""

from __future__ import annotations

import asyncio
import fcntl
import logging
import os
import stat
import tempfile
from collections.abc import AsyncIterator, Collection
from contextlib import asynccontextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Final

from ai.backend.logging import BraceStyleAdapter

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

DEFAULT_PAIR_JOURNAL_DIR: Final = Path("/var/lib/backend.ai/net-esp-pair")
#: Created like /tmp: any co-located agent may add its own claim, and the sticky bit stops it
#: removing anyone else's.
_SHARED_DIR_MODE: Final = 0o1777
#: Entries are group-readable so agents running as different users on one host can still count
#: each other's claims -- the whole point of the journal.
_ENTRY_MODE: Final = 0o644
#: The lock lives beside the data, on a file that is never renamed, replaced or removed.
_LOCK_SUFFIX: Final = ".lock"


@dataclass(frozen=True)
class _Held:
    """One pair's lock, held: the lock fd, and where its data lives."""

    fd: int
    path: Path
    root: Path


def pair_key(self_vtep: str, peer_vtep: str, dstport: int) -> str:
    """The journal's name for one pair. Directed, exactly as the SAs are."""
    return f"{self_vtep}_{peer_vtep}_{dstport}".replace(":", "-").replace("/", "-")


class PairJournal:
    """Node-wide users of each ESP pair, one file per pair, one ``owner/session`` per line."""

    _root: Path

    def __init__(self, root: Path | None = None) -> None:
        # Read through the module attribute, not captured at import: the node-global default is
        # what tests must be able to redirect, and a default argument would freeze it.
        self._root = root if root is not None else DEFAULT_PAIR_JOURNAL_DIR

    def _ensure_root(self) -> bool:
        try:
            self._root.mkdir(parents=True, exist_ok=True)
            self._root.chmod(_SHARED_DIR_MODE)
        except OSError:
            return False
        return True

    @asynccontextmanager
    async def claiming(self, key: str, owner: str, session_id: str) -> AsyncIterator[bool]:
        """Record this session's claim and hold the host lock while the caller programs the pair.

        One step on purpose. Between recording the claim and installing the SAs there is a window
        in which another agent can decide it is the last user and delete them, and the pair would
        then be open with nothing encrypting it.

        Yields whether the claim was actually recorded. False means the journal could not be
        written, and the caller must NOT program the pair: a claim that is not on disk is a claim
        another process cannot count, and it will remove the very SAs being installed.
        """
        async with self._hold(key) as held:
            if held is None:
                yield False
                return
            users = await asyncio.to_thread(self._read, held)
            if users is None:
                yield False
                return
            users.add(f"{owner}/{session_id}")
            yield await asyncio.to_thread(self._write, held, users)

    @asynccontextmanager
    async def releasing(self, key: str, owner: str, session_id: str) -> AsyncIterator[bool | None]:
        """Drop this claim and hold the host lock while the caller removes the pair.

        Yields whether the pair is now unused by anyone on this node: True to remove it, False to
        leave it, and None when that could not be determined -- which the caller must treat as
        "leave it". Of the two ways to be wrong, a stale SA keeps traffic encrypted while a
        deleted one takes down whoever else was on it.

        The lock spans the caller's block so the answer cannot go stale inside it.
        """
        async with self._hold(key) as held:
            if held is None:
                yield None
                return
            users = await asyncio.to_thread(self._read, held)
            if users is None:
                yield None
                return
            users.discard(f"{owner}/{session_id}")
            if not await asyncio.to_thread(self._write, held, users):
                # The claim may still be on disk, so another agent could still read us as a user.
                # Removing the SAs now would be removing them on an answer we did not publish.
                yield None
                return
            yield not users

    @asynccontextmanager
    async def _hold(self, key: str) -> AsyncIterator[_Held | None]:
        """The pair's exclusive host-wide lock, acquired off the event loop.

        The lock is taken on a file of its own that is never renamed, replaced or removed. It used
        to be taken on the data file, which `_write` replaces by rename -- so the moment a writer
        published its new version, the lock it still held was on an inode nobody would open again
        and the next process locked the new one straight away. Reproduced with two journal
        instances: the second entered `claiming()` while the first was inside `releasing()`.
        """
        held = await asyncio.to_thread(self._acquire, key)
        if held is None:
            yield None
            return
        try:
            yield held
        finally:
            await asyncio.to_thread(self._release_lock, held)

    def _acquire(self, key: str) -> _Held | None:
        if not self._ensure_root():
            return None
        lock_path = self._root / f"{key}{_LOCK_SUFFIX}"
        fd: int | None = None
        try:
            # O_NOFOLLOW: the directory is shared by every agent on the node, so a local user can
            # pre-create one of these predictable names as a symlink. Following it would have a
            # process holding CAP_DAC_OVERRIDE read and truncate whatever it points at.
            fd = os.open(lock_path, os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, _ENTRY_MODE)
            if not stat.S_ISREG(os.fstat(fd).st_mode):
                log.warning("ESP pair lock {} is not a regular file; ignoring it", lock_path)
                os.close(fd)
                return None
            fcntl.flock(fd, fcntl.LOCK_EX)
        except OSError as e:
            log.warning("ESP pair lock {} unavailable: {}", lock_path, e)
            if fd is not None:
                os.close(fd)
            return None
        return _Held(fd=fd, path=self._root / key, root=self._root)

    def _release_lock(self, held: _Held) -> None:
        try:
            fcntl.flock(held.fd, fcntl.LOCK_UN)
        finally:
            os.close(held.fd)

    def _read(self, held: _Held) -> set[str] | None:
        """The pair's users, or None when the file could not be read.

        None is not an empty set. An unreadable file answers "nobody is on this pair" if the two
        are conflated, and that answer authorises deleting an SA somebody else is using.

        Read through a fd opened here rather than by re-opening the name later: with the lock on a
        separate inode, the data name is the only thing left that a co-tenant could swap between
        the check and the read.
        """
        try:
            fd = os.open(held.path, os.O_RDONLY | os.O_NOFOLLOW)
        except FileNotFoundError:
            return set()  # nobody has claimed this pair yet
        except OSError as e:
            log.warning("could not read the ESP pair journal {}: {}", held.path, e)
            return None
        try:
            if not stat.S_ISREG(os.fstat(fd).st_mode):
                log.warning("ESP pair journal {} is not a regular file", held.path)
                return None
            with os.fdopen(fd, "r", encoding="utf-8") as handle:
                return {line.strip() for line in handle.read().splitlines() if line.strip()}
        except OSError as e:
            log.warning("could not read the ESP pair journal {}: {}", held.path, e)
            return None

    def _write(self, held: _Held, users: set[str]) -> bool:
        """Replace the pair's users. Returns whether it landed.

        Written to a unique temporary file and renamed, then the directory is fsynced: a crash
        mid-write must leave the previous set rather than a truncated one, because a half-written
        claim file reads as fewer users than there are -- the same failure as an unreadable one.
        The name is unique rather than pid-based, so a temporary left by a crash cannot make every
        later write fail on O_EXCL once that pid comes round again.

        An emptied pair is written empty rather than unlinked: the name stays stable, and nothing
        here has to reason about a file appearing and disappearing under a lock held elsewhere.
        """
        tmp: Path | None = None
        try:
            fd, tmp_name = tempfile.mkstemp(
                dir=held.root, prefix=f".{held.path.name}.", suffix=".tmp"
            )
            tmp = Path(tmp_name)
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                handle.write("\n".join(sorted(users)) + "\n" if users else "")
                handle.flush()
                os.fsync(handle.fileno())
            tmp.chmod(_ENTRY_MODE)
            tmp.replace(held.path)
            tmp = None
            self._fsync_dir(held.root)
            return True
        except OSError as e:
            log.warning("could not update the ESP pair journal {}: {}", held.path, e)
            return False
        finally:
            if tmp is not None:
                tmp.unlink(missing_ok=True)

    def _fsync_dir(self, root: Path) -> None:
        """Make the rename itself durable, not just the bytes it published."""
        try:
            fd = os.open(root, os.O_RDONLY | os.O_DIRECTORY)
        except OSError:
            return
        try:
            os.fsync(fd)
        except OSError:
            pass
        finally:
            os.close(fd)

    async def users(self, key: str) -> frozenset[str]:
        """Everyone on this node currently claiming the pair, for diagnostics."""
        async with self._hold(key) as held:
            if held is None:
                return frozenset()
            return frozenset(await asyncio.to_thread(self._read, held) or ())

    async def prune(self, owner: str, live_sessions: Collection[str]) -> int:
        """Drop ``owner``'s claims for sessions it no longer has. Returns how many went.

        Run at startup, because the claims outlive the process that made them: a crash between
        programming a pair and tearing it down leaves a claim with nobody behind it, and the pair
        it names is then never removed by anyone. Only this owner's rows are touched -- a
        co-located agent's claims are its own to settle, and treating them as dead is precisely
        the bug this journal exists to prevent.
        """
        prefix = f"{owner}/"
        removed = 0
        try:
            names = sorted(
                entry.name
                for entry in self._root.iterdir()
                if entry.is_file()
                and not entry.name.startswith(".")
                and not entry.name.endswith(_LOCK_SUFFIX)
            )
        except OSError:
            return 0
        for name in names:
            async with self._hold(name) as held:
                if held is None:
                    continue
                users = await asyncio.to_thread(self._read, held)
                if users is None:
                    continue
                stale = {
                    user
                    for user in users
                    if user.startswith(prefix) and user[len(prefix) :] not in live_sessions
                }
                if not stale:
                    continue
                if await asyncio.to_thread(self._write, held, users - stale):
                    removed += len(stale)
        return removed
