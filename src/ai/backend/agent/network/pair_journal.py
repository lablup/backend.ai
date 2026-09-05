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
import contextlib
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
#: Ordinary directory permissions, deliberately NOT world-writable.
#:
#: It was 0o1777 so agents running as different users could each add claims. That is a weaker
#: boundary than it looks: a local user who creates a pair's directory first OWNS it, and can then
#: unlink and recreate the `.lock` inside -- after which a second holder locks the NEW inode while
#: the first still holds the old one, and both are in the critical section at once. Reproduced.
#:
#: So the namespace is closed instead. The mode carries GROUP write on purpose: the deployment
#: contract is that every agent sharing a host runs as the same user OR shares a group, and 0o755
#: would have made the second half of that a promise the permissions did not keep. Its parent,
#: /var/lib/backend.ai, is already owner-writable only, so no unprivileged user can create the
#: root either. `unusable_reason` probes an actual write rather than trusting any of this.
_JOURNAL_DIR_MODE: Final = 0o2775
#: The lock is only ever opened read-only, but it must be readable by every agent on the node --
#: and `os.open`'s mode is masked by umask, which is 0o077 on a hardened host. It is set
#: explicitly with `fchmod` after creation, on the descriptor, so no name is re-resolved.
_LOCK_MODE: Final = 0o664
_LOCK_NAME: Final = ".lock"
#: Claim files are readable by every agent so they can count each other's; only their owner ever
#: creates or removes one.
_CLAIM_MODE: Final = 0o664
#: Separates the two halves of a claim's filename. Neither an agent id nor a session id contains
#: it, and it cannot be confused with the path separator they are sanitised of.
_CLAIM_SEP: Final = "~"
#: How long to wait between attempts at a lock another process holds. Non-blocking attempts in a
#: loop, rather than one blocking call: a blocking `flock` handed to a thread outlives the task
#: that is cancelled while waiting for it, and then acquires a lock nobody is left to release.
_LOCK_POLL_SEC: Final = 0.05
#: How long to keep trying for a lock another process holds. A holder that crashed releases it
#: with its fd, so waiting is normally brief; a holder wedged inside a privileged command does not,
#: and the waiter is under the privnet's node-wide barrier. Giving up is reported as "could not
#: take the lock", which every caller already treats as "not permission".
_LOCK_WAIT_TIMEOUT_SEC: Final = 60.0


def pair_key(self_vtep: str, peer_vtep: str, dstport: int) -> str:
    """The journal's name for one pair's OUTBOUND POLICY. Directed, exactly as the SAs are.

    Per port, because the policy selector names the port: a session on another port needs its own.
    """
    return f"{self_vtep}_{peer_vtep}_{dstport}".replace(":", "-").replace("/", "-")


def sa_key(self_vtep: str, peer_vtep: str) -> str:
    """The journal's name for one pair's SAs.

    Deliberately without the port. An SA carries no port -- the kernel identifies it by
    (dst, spi, proto) and it is created with neither -- so every session between these two nodes
    rides the same one whatever port its overlay runs on. Counting SA users per port lets the last
    session on one port delete the SAs a session on another port is still sending through, leaving
    that session's policy selecting an SA that no longer exists.
    """
    return f"{self_vtep}_{peer_vtep}_sa".replace(":", "-").replace("/", "-")


def _claim_name(owner: str, session_id: str) -> str:
    return f"{_sanitise(owner)}{_CLAIM_SEP}{_sanitise(session_id)}"


def _sanitise(value: str) -> str:
    return value.replace("/", "-").replace(_CLAIM_SEP, "-")


@dataclass(frozen=True)
class ClaimSet:
    """One key's claims, with the node-wide lock held: read them, add or drop this owner's.

    Handed out by `holding` so a caller that must DECIDE from the existing claims before making
    its own -- "is this VNI already another session's?" -- can do both inside one critical
    section. Reading and then claiming as two calls is two locks with a gap between them, and the
    gap is where two agents both read "free" and both claim.
    """

    _journal: PairJournal
    _held: _Held

    def users(self) -> frozenset[str] | None:
        """``owner/session`` for everyone claiming this key, or None if it could not be listed.

        None is not an empty set: an unlistable directory answering "nobody" is what authorises
        taking something somebody else is using.
        """
        claims = self._journal._claims(self._held)
        if claims is None:
            return None
        return frozenset(name.replace(_CLAIM_SEP, "/", 1) for name in claims)

    def add(self, owner: str, session_id: str) -> bool:
        return self._journal._write_claim(self._held, owner, session_id)

    def remove(self, owner: str, session_id: str) -> bool:
        return self._journal._remove_claim(self._held, owner, session_id)


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
    """Node-wide users of each ESP pair: a directory per pair, a file per claim.

    Node-wide among agents that share a user (or a group with write access to the tree). That is a
    deployment contract, not an implementation detail -- see `_JOURNAL_DIR_MODE` for why the
    world-writable alternative could not hold the guarantee it appeared to.
    """

    _root: Path

    def __init__(self, root: Path | None = None) -> None:
        # Read through the module attribute, not captured at import: the node-global default is
        # what tests must be able to redirect, and a default argument would freeze it.
        self._root = root if root is not None else DEFAULT_PAIR_JOURNAL_DIR

    def unusable_reason(self) -> str | None:
        """Why this node cannot use the pair journal, or None if it can.

        Checked at startup rather than at the first session: without the journal a co-located
        agent's claims cannot be counted, and every encrypted peer is refused (`claiming` returns
        False and the caller fails closed) -- which is correct, and useless to debug from a
        per-session error.

        It WRITES, rather than only opening the root. Opening proves the directory is there; it
        does not prove this process can create a claim in it, which is the operation everything
        depends on -- and on a host where the agents run as different users under a shared group,
        those are different questions.
        """
        fd = self._open_root()
        if fd is None:
            return (
                f"the ESP pair journal {self._root} cannot be created or opened; without it this"
                " node cannot tell whether a co-located agent is still using a peer's SAs, so"
                " every encrypted peer is refused. Its parent must be writable by the user the"
                " agent runs as, and every agent on this host must share that user or a group"
                " with write access to the tree."
            )
        try:
            mode = stat.S_IMODE(os.fstat(fd).st_mode)
            if mode & stat.S_IWOTH:
                # An older version created this tree world-writable. A local user who owns a pair
                # directory inside it can unlink and recreate the lock, which puts two holders in
                # the critical section at once -- so it is refused rather than silently used.
                return (
                    f"the ESP pair journal {self._root} is world-writable ({mode:04o}). A local"
                    " user can then own a pair's directory and replace the lock inside it, which"
                    f" defeats the lock entirely. Remove it (it is rebuilt empty) or chmod it to"
                    f" {_JOURNAL_DIR_MODE:04o}."
                )
            if (unwritable := self._probe_write(fd)) is not None:
                return unwritable
        finally:
            os.close(fd)
        return None

    def _probe_write(self, root_fd: int) -> str | None:
        """Create and remove a file in the journal root; the reason it could not, or None.

        Opening the root proves it is there, not that this process can create a claim in it --
        which is the operation everything depends on, and a different question on a host where
        the agents run as different users under a shared group.
        """
        probe = f".probe.{os.getpid()}"
        try:
            probe_fd = os.open(
                probe, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=root_fd
            )
        except OSError as e:
            return (
                f"the ESP pair journal {self._root} cannot be written by this agent ({e}), so it"
                " cannot record which peers it is using and every encrypted peer is refused."
                " Every agent on this host must run as the user that owns this tree, or share a"
                " group with write access to it."
            )
        os.close(probe_fd)
        with contextlib.suppress(OSError):
            os.unlink(probe, dir_fd=root_fd)
        return None

    def _open_root(self) -> int | None:
        """A descriptor on the journal root.

        The mode is set explicitly because `mkdir(parents=True)` gives the intermediate
        directories the process umask, and this tree's permissions are the boundary -- see
        `_JOURNAL_DIR_MODE`.
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
            os.fchmod(fd, _JOURNAL_DIR_MODE)
        except OSError as e:
            # Not "already correct": it may be somebody else's, with a mode we would not have
            # chosen. `unusable_reason` is what decides, by looking and by writing.
            log.debug("could not set the mode of the ESP pair journal root: {}", e)
        return fd

    def _open_pair(self, root_fd: int, key: str) -> int | None:
        """A descriptor on one pair's directory, opened relative to the root and never followed.

        Every step is relative to a descriptor whose inode has already been verified, and each
        open refuses a symlink. Resolving the path by name instead is what let a pre-created
        symlink at the pair's name have this process chmod SOMEBODY ELSE'S directory to 0o1777 and
        fill it with files -- reproduced, with a 0o700 directory coming back 0o1777.
        """
        try:
            os.mkdir(key, mode=_JOURNAL_DIR_MODE, dir_fd=root_fd)
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
            os.fchmod(fd, _JOURNAL_DIR_MODE)
        except OSError as e:
            log.debug("could not set the mode of the ESP pair directory {}: {}", key, e)
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
        async with self.holding(key) as claims:
            if claims is None:
                yield False
                return
            yield claims.add(owner, session_id)

    @asynccontextmanager
    async def releasing(self, key: str, owner: str, session_id: str) -> AsyncIterator[bool | None]:
        """Drop this claim and hold the host lock while the caller removes the pair.

        Yields whether the pair is now unused by anyone on this node: True to remove it, False to
        leave it, and None when that could not be determined -- which the caller must treat as
        "leave it". Of the two ways to be wrong, a stale SA keeps traffic encrypted while a
        deleted one takes down whoever else was on it.

        The lock spans the caller's block so the answer cannot go stale inside it.
        """
        async with self.holding(key) as claims:
            if claims is None:
                yield None
                return
            if not claims.remove(owner, session_id):
                yield None
                return
            remaining = claims.users()
            yield None if remaining is None else not remaining

    async def users(self, key: str) -> frozenset[str]:
        """Everyone on this node currently claiming the key, for diagnostics."""
        async with self.holding(key) as claims:
            return frozenset() if claims is None else (claims.users() or frozenset())

    @asynccontextmanager
    async def holding(self, key: str) -> AsyncIterator[ClaimSet | None]:
        """This key's claims with the node-wide lock held for the caller's block.

        None means the lock could not be taken, which is never permission to act.
        """
        async with self._hold(key) as held:
            yield None if held is None else ClaimSet(self, held)

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
            with os.scandir(root_fd) as entries:
                pairs = sorted(entry.name for entry in entries)
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
        deadline = asyncio.get_running_loop().time() + _LOCK_WAIT_TIMEOUT_SEC
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
                if e.errno not in (errno.EAGAIN, errno.EWOULDBLOCK):
                    os.close(dir_fd)
                    log.warning("could not lock the ESP pair {}: {}", key, e)
                    return None
                if asyncio.get_running_loop().time() >= deadline:
                    os.close(dir_fd)
                    log.warning(
                        "gave up waiting {}s for the node-wide lock on {}; a holder is wedged",
                        _LOCK_WAIT_TIMEOUT_SEC,
                        key,
                    )
                    return None
                # Somebody else has it. Waiting here is cancellable, which is the point -- and
                # the directory descriptor has to be closed if the wait IS cancelled, or every
                # cancelled waiter keeps one and the process walks into its RLIMIT_NOFILE.
                # Measured before this: 50 cancelled waiters, 50 descriptors left behind.
                try:
                    await asyncio.sleep(_LOCK_POLL_SEC)
                except BaseException:
                    os.close(dir_fd)
                    raise
                continue
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
            with os.scandir(held.dir_fd) as entries:
                return {
                    entry.name
                    for entry in entries
                    if entry.name != _LOCK_NAME and not entry.name.startswith(".")
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
