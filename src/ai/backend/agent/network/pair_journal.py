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
#: The lock is only ever opened read-only, but it must be readable by every agent on the node --
#: and `os.open`'s mode is masked by umask, which is 0o077 on a hardened host. It is set
#: explicitly with `fchmod` after creation, on the descriptor, so no name is re-resolved.
_LOCK_MODE: Final = 0o644
_LOCK_NAME: Final = ".lock"
#: Claim files are readable by every agent so they can count each other's; only their owner ever
#: creates or removes one.
_CLAIM_MODE: Final = 0o644
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
    """One pair's lock, held: the lock's fd and a verified descriptor on its directory.

    A descriptor, not a path. Everything done under the lock is done relative to it, so no name
    is resolved a second time and nothing can be swapped underneath between the check and the use.
    """

    lock_fd: int
    dir_fd: int
    key: str


class PairJournal:
    """Node-wide users of each ESP pair: a directory per pair, a file per claim."""

    _root: Path

    def __init__(self, root: Path | None = None) -> None:
        # Read through the module attribute, not captured at import: the node-global default is
        # what tests must be able to redirect, and a default argument would freeze it.
        self._root = root if root is not None else DEFAULT_PAIR_JOURNAL_DIR

    def _open_root(self) -> int | None:
        """A descriptor on the journal root, created world-writable-sticky like /tmp.

        The root itself has to carry the mode: `mkdir(parents=True)` gives the intermediate
        directories the process umask, and a root at 0o775 is one that a co-located agent running
        as another user cannot create a new pair in -- which is the whole point of the journal.
        """
        try:
            self._root.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            log.warning("ESP pair journal root {} unavailable: {}", self._root, e)
            return None
        try:
            fd = os.open(self._root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        except OSError as e:
            log.warning("ESP pair journal root {} is not a usable directory: {}", self._root, e)
            return None
        try:
            os.fchmod(fd, _SHARED_DIR_MODE)
        except OSError:
            pass  # another user created it; it already carries the mode we would have set
        return fd

    def _open_pair(self, root_fd: int, key: str) -> int | None:
        """A descriptor on one pair's directory, opened relative to the root and never followed.

        Every step is relative to a descriptor whose inode has already been verified, and each
        open refuses a symlink. Resolving the path by name instead is what let a pre-created
        symlink at the pair's name have this process chmod SOMEBODY ELSE'S directory to 0o1777 and
        fill it with files -- reproduced, with a 0o700 directory coming back 0o1777.
        """
        try:
            os.mkdir(key, mode=_SHARED_DIR_MODE, dir_fd=root_fd)
        except FileExistsError:
            pass
        except OSError as e:
            log.warning("could not create the ESP pair directory {}: {}", key, e)
            return None
        try:
            fd = os.open(key, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=root_fd)
        except OSError as e:
            # ELOOP here is the attack above, refused.
            log.warning("ESP pair directory {} is not a usable directory: {}", key, e)
            return None
        try:
            os.fchmod(fd, _SHARED_DIR_MODE)
        except OSError:
            pass  # created by another user, already sticky
        return fd

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
        root_fd = self._open_root()
        if root_fd is None:
            return 0
        try:
            # Listed through the verified descriptor, and each name is opened with O_NOFOLLOW by
            # `_open_pair` below -- a symlink planted at a pair's name is refused there.
            pairs = sorted(os.listdir(root_fd))
        except OSError:
            return 0
        finally:
            os.close(root_fd)
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
                        os.unlink(name, dir_fd=held.dir_fd)
                        removed += 1
                    except FileNotFoundError:
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
        root_fd = self._open_root()
        if root_fd is None:
            return None
        try:
            dir_fd = self._open_pair(root_fd, key)
        finally:
            os.close(root_fd)
        if dir_fd is None:
            return None
        while True:
            lock_fd: int | None = None
            try:
                # Relative to the verified directory, never followed, and NON-BLOCKING: an
                # attacker who pre-creates the predictable `.lock` name as a FIFO makes a plain
                # `open` wait for a writer that never comes -- which stops the whole process, not
                # just this coroutine. Reproduced: the interpreter hung until it was killed.
                # O_NOFOLLOW does not cover this; O_NONBLOCK plus the regular-file check does.
                lock_fd = os.open(
                    _LOCK_NAME,
                    os.O_RDONLY | os.O_CREAT | os.O_NOFOLLOW | os.O_NONBLOCK,
                    _LOCK_MODE,
                    dir_fd=dir_fd,
                )
                if not stat.S_ISREG(os.fstat(lock_fd).st_mode):
                    log.warning("ESP pair lock for {} is not a regular file; ignoring it", key)
                    os.close(lock_fd)
                    os.close(dir_fd)
                    return None
                # Explicitly, on the descriptor: `open`'s mode is masked by umask, and a lock at
                # 0o600 is one no other agent on the node can open at all.
                try:
                    os.fchmod(lock_fd, _LOCK_MODE)
                except OSError:
                    pass  # somebody else owns it and already set the mode
            except OSError as e:
                if lock_fd is not None:
                    os.close(lock_fd)
                os.close(dir_fd)
                # A permission error is NOT contention. Treating the two alike is how a node with
                # a mis-owned journal polls forever instead of reporting that it cannot serve.
                log.warning("ESP pair lock for {} unavailable: {}", key, e)
                return None
            try:
                fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except OSError as e:
                os.close(lock_fd)
                if e.errno in (errno.EAGAIN, errno.EWOULDBLOCK):
                    # Somebody else has it. Waiting here is cancellable, which is the point.
                    await asyncio.sleep(_LOCK_POLL_SEC)
                    continue
                os.close(dir_fd)
                log.warning("could not lock the ESP pair {}: {}", key, e)
                return None
            return _Held(lock_fd=lock_fd, dir_fd=dir_fd, key=key)

    def _release_lock(self, held: _Held) -> None:
        try:
            fcntl.flock(held.lock_fd, fcntl.LOCK_UN)
        finally:
            os.close(held.lock_fd)
            os.close(held.dir_fd)

    def _claims(self, held: _Held) -> set[str] | None:
        """Every claim file in the pair's directory, or None if it could not be listed.

        None is not an empty set. An unlistable directory answers "nobody is on this pair" if the
        two are conflated, and that answer authorises deleting an SA somebody else is using.
        """
        try:
            return {
                name
                for name in os.listdir(held.dir_fd)
                if name != _LOCK_NAME and not name.startswith(".")
            }
        except OSError as e:
            log.warning("could not list the ESP pair claims for {}: {}", held.key, e)
            return None

    def _write_claim(self, held: _Held, owner: str, session_id: str) -> bool:
        name = _claim_name(owner, session_id)
        try:
            # Its own file, created and later removed by this owner alone: nothing here ever
            # rewrites another user's file, so the sticky bit protects each agent's claims
            # instead of blocking them.
            fd = os.open(
                name,
                os.O_WRONLY | os.O_CREAT | os.O_NOFOLLOW | os.O_NONBLOCK,
                _CLAIM_MODE,
                dir_fd=held.dir_fd,
            )
        except OSError as e:
            log.warning("could not record the ESP pair claim {}: {}", name, e)
            return False
        os.close(fd)
        return True

    def _remove_claim(self, held: _Held, owner: str, session_id: str) -> bool:
        name = _claim_name(owner, session_id)
        try:
            os.unlink(name, dir_fd=held.dir_fd)
        except FileNotFoundError:
            return True  # already gone; the claim is what matters, not the unlink
        except OSError as e:
            log.warning("could not drop the ESP pair claim {}: {}", name, e)
            return False
        return True
