"""Who on this NODE is using a given ESP pair, durably and across processes.

An SA and its policy belong to a (self VTEP, peer VTEP, underlay port) triple, and every session
between those two nodes on that port shares them. The refcount deciding when they may be removed
therefore has to be node-wide -- but it lived in one process's memory, which is only node-wide in
the deployment where a single privnet owns the host's networking. Where each agent runs the
backend in-process instead, two agents on one host each believed they were the pair's only user,
and the first session to end took the other's protection with it.

Shape: a directory per pair, and inside it ONE FILE PER CLAIM, created and removed by the agent
that made it. Nothing rewrites anybody else's file, which is what makes this work between agents
running as different users -- a shared file replaced by rename cannot be, because the sticky bit
on a world-writable directory (correctly) refuses to let one user replace another's file, and the
lock on such a file dies with the inode the rename retires. The lock is a separate name that is
never removed, opened read-only: `flock` needs no write access, only a file descriptor.
"""

from __future__ import annotations

import asyncio
import errno
import fcntl
import logging
import os
import stat
from collections.abc import AsyncIterator, Collection
from contextlib import asynccontextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Final

from ai.backend.logging import BraceStyleAdapter

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

DEFAULT_PAIR_JOURNAL_DIR: Final = Path("/var/lib/backend.ai/net-esp-pair")
#: Created like /tmp: any co-located agent may add its own claim, and the sticky bit stops it
#: removing anyone else's -- which is exactly the guarantee this journal needs.
_SHARED_DIR_MODE: Final = 0o1777
#: The lock is only ever opened read-only, so this need not be writable by other users.
_LOCK_MODE: Final = 0o644
_LOCK_NAME: Final = ".lock"
#: Separates the two halves of a claim's filename. Neither an agent id nor a session id contains
#: it, and it cannot be confused with the path separator they are sanitised of.
_CLAIM_SEP: Final = "~"
#: How long to wait between attempts at a lock another process holds. Non-blocking attempts in a
#: loop, rather than one blocking call: a blocking `flock` handed to a thread outlives the task
#: that is cancelled while waiting for it, and then acquires a lock nobody is left to release.
_LOCK_POLL_SEC: Final = 0.05


def pair_key(self_vtep: str, peer_vtep: str, dstport: int) -> str:
    """The journal's name for one pair. Directed, exactly as the SAs are."""
    return f"{self_vtep}_{peer_vtep}_{dstport}".replace(":", "-").replace("/", "-")


def _claim_name(owner: str, session_id: str) -> str:
    return f"{_sanitise(owner)}{_CLAIM_SEP}{_sanitise(session_id)}"


def _sanitise(value: str) -> str:
    return value.replace("/", "-").replace(_CLAIM_SEP, "-")


@dataclass(frozen=True)
class _Held:
    """One pair's lock, held: the lock's fd and the directory its claims live in."""

    fd: int
    directory: Path


class PairJournal:
    """Node-wide users of each ESP pair: a directory per pair, a file per claim."""

    _root: Path

    def __init__(self, root: Path | None = None) -> None:
        # Read through the module attribute, not captured at import: the node-global default is
        # what tests must be able to redirect, and a default argument would freeze it.
        self._root = root if root is not None else DEFAULT_PAIR_JOURNAL_DIR

    def _ensure_dir(self, path: Path) -> bool:
        try:
            path.mkdir(parents=True, exist_ok=True)
            path.chmod(_SHARED_DIR_MODE)
        except OSError as e:
            # chmod fails for a directory another user created; that is fine, it already has the
            # mode we would have set. Only a directory we cannot get at all is a problem.
            if not path.is_dir():
                log.warning("ESP pair journal directory {} unavailable: {}", path, e)
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
            yield self._write_claim(held, owner, session_id)

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
            if not self._remove_claim(held, owner, session_id):
                yield None
                return
            remaining = self._claims(held)
            yield None if remaining is None else not remaining

    async def users(self, key: str) -> frozenset[str]:
        """Everyone on this node currently claiming the pair, for diagnostics."""
        async with self._hold(key) as held:
            if held is None:
                return frozenset()
            claims = self._claims(held) or set()
            return frozenset(name.replace(_CLAIM_SEP, "/", 1) for name in claims)

    async def prune(self, owner: str, live_sessions: Collection[str]) -> int:
        """Drop ``owner``'s claims for sessions it no longer has. Returns how many went.

        Claims outlive the process that made them: a crash between programming a pair and tearing
        it down leaves one with nobody behind it, and the pair it names is then never removed by
        anyone. Only this owner's own files are unlinked -- a co-located agent's claims are its
        own to settle, and the sticky bit would refuse anyway.
        """
        live = {_sanitise(session_id) for session_id in live_sessions}
        prefix = f"{_sanitise(owner)}{_CLAIM_SEP}"
        removed = 0
        try:
            pairs = sorted(entry.name for entry in self._root.iterdir() if entry.is_dir())
        except OSError:
            return 0
        for pair in pairs:
            async with self._hold(pair) as held:
                if held is None:
                    continue
                claims = self._claims(held)
                if claims is None:
                    continue
                for name in sorted(claims):
                    if not name.startswith(prefix) or name[len(prefix) :] in live:
                        continue
                    try:
                        (held.directory / name).unlink(missing_ok=True)
                        removed += 1
                    except OSError as e:
                        log.warning("could not drop the stale ESP pair claim {}: {}", name, e)
        return removed

    @asynccontextmanager
    async def _hold(self, key: str) -> AsyncIterator[_Held | None]:
        """The pair's exclusive host-wide lock.

        Acquired with repeated non-blocking attempts rather than one blocking call handed to a
        thread. A blocking `flock` in a worker outlives the task cancelled while awaiting it: the
        thread goes on to take the lock, and the coroutine that would have released it is gone --
        after which every create and delete for that node pair stops until the process restarts.
        Reproduced.
        """
        held = await self._acquire(key)
        if held is None:
            yield None
            return
        try:
            yield held
        finally:
            self._release_lock(held)

    async def _acquire(self, key: str) -> _Held | None:
        directory = self._root / key
        if not self._ensure_dir(directory):
            return None
        lock_path = directory / _LOCK_NAME
        while True:
            fd: int | None = None
            try:
                # Read-only: `flock` needs a descriptor, not write access, and a co-located agent
                # running as another user cannot open the first one's lock file for writing.
                # O_NOFOLLOW because the directory is shared and the name is predictable.
                fd = os.open(lock_path, os.O_RDONLY | os.O_CREAT | os.O_NOFOLLOW, _LOCK_MODE)
                if not stat.S_ISREG(os.fstat(fd).st_mode):
                    log.warning("ESP pair lock {} is not a regular file; ignoring it", lock_path)
                    os.close(fd)
                    return None
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except OSError as e:
                if fd is not None:
                    os.close(fd)
                if e.errno in (errno.EACCES, errno.EAGAIN):
                    # Somebody else has it. Waiting here is cancellable, which is the point.
                    await asyncio.sleep(_LOCK_POLL_SEC)
                    continue
                log.warning("ESP pair lock {} unavailable: {}", lock_path, e)
                return None
            return _Held(fd=fd, directory=directory)

    def _release_lock(self, held: _Held) -> None:
        try:
            fcntl.flock(held.fd, fcntl.LOCK_UN)
        finally:
            os.close(held.fd)

    def _claims(self, held: _Held) -> set[str] | None:
        """Every claim file in the pair's directory, or None if it could not be listed.

        None is not an empty set. An unlistable directory answers "nobody is on this pair" if the
        two are conflated, and that answer authorises deleting an SA somebody else is using.
        """
        try:
            return {
                entry.name
                for entry in held.directory.iterdir()
                if entry.name != _LOCK_NAME and not entry.name.startswith(".")
            }
        except OSError as e:
            log.warning("could not list the ESP pair claims in {}: {}", held.directory, e)
            return None

    def _write_claim(self, held: _Held, owner: str, session_id: str) -> bool:
        path = held.directory / _claim_name(owner, session_id)
        try:
            # Its own file, created and later removed by this owner alone: nothing here ever
            # rewrites another user's file, so the sticky bit protects each agent's claims
            # instead of blocking them.
            fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_NOFOLLOW, 0o644)
        except OSError as e:
            log.warning("could not record the ESP pair claim {}: {}", path, e)
            return False
        os.close(fd)
        return True

    def _remove_claim(self, held: _Held, owner: str, session_id: str) -> bool:
        path = held.directory / _claim_name(owner, session_id)
        try:
            path.unlink(missing_ok=True)
        except OSError as e:
            log.warning("could not drop the ESP pair claim {}: {}", path, e)
            return False
        return True
