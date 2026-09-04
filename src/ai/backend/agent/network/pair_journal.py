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
from collections.abc import AsyncIterator, Collection
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Final

from ai.backend.logging import BraceStyleAdapter

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

DEFAULT_PAIR_JOURNAL_DIR: Final = Path("/var/lib/backend.ai/net-esp-pair")
#: Created like /tmp: any co-located agent may add its own claim, and the sticky bit stops it
#: removing anyone else's.
_SHARED_DIR_MODE: Final = 0o1777


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
        written -- the caller may still program, but must never later conclude from this journal
        that the pair is free.
        """
        async with self._hold(key) as path:
            if path is None:
                yield False
                return
            users = await asyncio.to_thread(self._read, path)
            if users is None:
                yield False
                return
            users.add(f"{owner}/{session_id}")
            yield await asyncio.to_thread(self._write, path, users)

    @asynccontextmanager
    async def releasing(self, key: str, owner: str, session_id: str) -> AsyncIterator[bool | None]:
        """Drop this claim and hold the host lock while the caller removes the pair.

        Yields whether the pair is now unused by anyone on this node: True to remove it, False to
        leave it, and None when that could not be determined -- which the caller must treat as
        "leave it". Of the two ways to be wrong, a stale SA keeps traffic encrypted while a
        deleted one takes down whoever else was on it.

        The lock spans the caller's block so the answer cannot go stale inside it.
        """
        async with self._hold(key) as path:
            if path is None:
                yield None
                return
            users = await asyncio.to_thread(self._read, path)
            if users is None:
                yield None
                return
            users.discard(f"{owner}/{session_id}")
            if not await asyncio.to_thread(self._write, path, users):
                # The claim may still be on disk, so another agent could still read us as a user.
                # Removing the SAs now would be removing them on an answer we did not manage to
                # publish.
                yield None
                return
            yield not users

    @asynccontextmanager
    async def _hold(self, key: str) -> AsyncIterator[Path | None]:
        """The pair's exclusive host-wide lock, acquired off the event loop."""
        opened = await asyncio.to_thread(self._open_locked, key)
        if opened is None:
            yield None
            return
        fd, path = opened
        try:
            yield path
        finally:
            await asyncio.to_thread(self._unlock, fd)

    def _open_locked(self, key: str) -> tuple[int, Path] | None:
        if not self._ensure_root():
            return None
        path = self._root / key
        fd: int | None = None
        try:
            # O_NOFOLLOW: the directory is shared by every agent on the node, so a local user can
            # pre-create one of these predictable names as a symlink. Following it would have a
            # process holding CAP_DAC_OVERRIDE read and truncate whatever it points at.
            fd = os.open(path, os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
            if not stat.S_ISREG(os.fstat(fd).st_mode):
                log.warning("ESP pair journal entry {} is not a regular file; ignoring it", path)
                os.close(fd)
                return None
            fcntl.flock(fd, fcntl.LOCK_EX)
        except OSError as e:
            log.warning("ESP pair journal {} unavailable: {}", path, e)
            if fd is not None:
                os.close(fd)
            return None
        return fd, path

    def _unlock(self, fd: int) -> None:
        try:
            fcntl.flock(fd, fcntl.LOCK_UN)
        finally:
            os.close(fd)

    def _read(self, path: Path) -> set[str] | None:
        """The pair's users, or None when the file could not be read.

        None is not an empty set. An unreadable file answers "nobody is on this pair" if the two
        are conflated, and that answer authorises deleting an SA somebody else is using.
        """
        try:
            return {line.strip() for line in path.read_text().splitlines() if line.strip()}
        except OSError as e:
            log.warning("could not read the ESP pair journal {}: {}", path, e)
            return None

    def _write(self, path: Path, users: set[str]) -> bool:
        """Replace the pair's users. Returns whether it landed.

        Written to a temporary file and renamed, so a crash mid-write leaves the previous set
        rather than a truncated one: a half-written claim file reads as fewer users than there
        are, which is the same failure as an unreadable one.
        """
        try:
            if not users:
                path.unlink(missing_ok=True)
                return True
            tmp = path.with_name(f".{path.name}.{os.getpid()}.tmp")
            fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
            try:
                with os.fdopen(fd, "w", encoding="utf-8") as handle:
                    handle.write("\n".join(sorted(users)) + "\n")
                    handle.flush()
                    os.fsync(handle.fileno())
            except BaseException:
                tmp.unlink(missing_ok=True)
                raise
            tmp.replace(path)
            return True
        except OSError as e:
            log.warning("could not update the ESP pair journal {}: {}", path, e)
            return False

    async def users(self, key: str) -> frozenset[str]:
        """Everyone on this node currently claiming the pair, for diagnostics."""
        async with self._hold(key) as path:
            if path is None:
                return frozenset()
            return frozenset(await asyncio.to_thread(self._read, path) or ())

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
            names = sorted(entry.name for entry in self._root.iterdir() if entry.is_file())
        except OSError:
            return 0
        for name in names:
            if name.startswith("."):
                continue  # a interrupted write's temporary file
            async with self._hold(name) as path:
                if path is None:
                    continue
                users = await asyncio.to_thread(self._read, path)
                if users is None:
                    continue
                stale = {
                    user
                    for user in users
                    if user.startswith(prefix) and user[len(prefix) :] not in live_sessions
                }
                if not stale:
                    continue
                if await asyncio.to_thread(self._write, path, users - stale):
                    removed += len(stale)
        return removed
