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

import fcntl
import logging
from collections.abc import Collection, Iterator
from contextlib import contextmanager
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

    @contextmanager
    def _locked(self, key: str) -> Iterator[Path | None]:
        """The pair's file, with an exclusive lock held across read-modify-write.

        A journal this cannot open is not a reason to refuse the operation -- the in-process
        refcount still bounds it to the single-owner case, which is what every deployment had
        before this existed. It yields None and the caller falls back.
        """
        if not self._ensure_root():
            yield None
            return
        path = self._root / key
        try:
            with path.open("a+", encoding="utf-8") as handle:
                fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
                try:
                    yield path
                finally:
                    fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
        except OSError as e:
            log.debug("ESP pair journal {} unavailable: {}", path, e)
            yield None

    def _read(self, path: Path) -> set[str]:
        try:
            return {line.strip() for line in path.read_text().splitlines() if line.strip()}
        except OSError:
            return set()

    def _write(self, path: Path, users: set[str]) -> None:
        try:
            if users:
                path.write_text("\n".join(sorted(users)) + "\n")
            else:
                path.unlink(missing_ok=True)
        except OSError as e:
            log.warning("could not update the ESP pair journal {}: {}", path, e)

    def claim(self, key: str, owner: str, session_id: str) -> None:
        """Record that ``owner``'s session is carried by this pair."""
        with self._locked(key) as path:
            if path is None:
                return
            users = self._read(path)
            users.add(f"{owner}/{session_id}")
            self._write(path, users)

    def release(self, key: str, owner: str, session_id: str) -> bool | None:
        """Drop this session's claim; return whether the pair is now unused by anyone on the node.

        None means the journal could not be consulted, and the caller decides with what it has.
        """
        with self._locked(key) as path:
            if path is None:
                return None
            users = self._read(path)
            users.discard(f"{owner}/{session_id}")
            self._write(path, users)
            return not users

    def users(self, key: str) -> frozenset[str]:
        """Everyone on this node currently claiming the pair, for diagnostics."""
        with self._locked(key) as path:
            if path is None:
                return frozenset()
            return frozenset(self._read(path))

    def prune(self, owner: str, live_sessions: Collection[str]) -> int:
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
            with self._locked(name) as path:
                if path is None:
                    continue
                users = self._read(path)
                stale = {
                    user
                    for user in users
                    if user.startswith(prefix) and user[len(prefix) :] not in live_sessions
                }
                if not stale:
                    continue
                removed += len(stale)
                self._write(path, users - stale)
        return removed
