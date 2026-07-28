"""Crash-atomic writes for the node-local network journals (BEP-1062).

The IPAM and LOCAL-subnet allocators journal each claim as a small file whose existence *and*
content are authoritative across a restart. A plain create-then-write (``open("x")`` then
``write``, or ``write_text``) leaves an empty or truncated file if the process is killed between the
two -- which this often-restarted daemon is -- and replay then reads a claim owned by ``""`` (a
leaked address/block) or an unreadable layout marker (which fails block allocation node-wide). A
claim must land atomically: the file is either absent or complete, never partial.

Temp files are dot-prefixed (``.tmp-<name>.<pid>``); a crash between the atomic link/replace and the
temp's unlink can leave one behind, so **every replay must skip dot-prefixed names**.
"""

from __future__ import annotations

import contextlib
import os
from pathlib import Path


def _fsync_write(tmp: Path, content: str) -> None:
    """Write ``content`` to ``tmp`` and flush it to disk, so the subsequent link/replace publishes a
    file whose bytes are already durable rather than sitting in a buffer a crash would drop."""
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o644)
    try:
        os.write(fd, content.encode())
        os.fsync(fd)
    finally:
        os.close(fd)


def _temp_path(path: Path) -> Path:
    # Dot-prefixed and pid-scoped: replay skips it, and two writers never collide on the temp name.
    return path.with_name(f".tmp-{path.name}.{os.getpid()}")


def atomic_exclusive_write(path: Path, content: str) -> None:
    """Create ``path`` with ``content`` atomically *and* exclusively.

    A crash leaves ``path`` absent or complete, never empty. An already-existing ``path`` raises
    ``FileExistsError`` -- the caller's "another writer already owns this" signal, exactly as the
    old ``open("x")`` gave. The content is written to a temp sibling and fsynced, then hard-linked
    into place: ``os.link`` is atomic and fails if the target exists, giving both properties at once.
    """
    tmp = _temp_path(path)
    try:
        _fsync_write(tmp, content)
        os.link(tmp, path)
    finally:
        with contextlib.suppress(OSError):
            tmp.unlink()


def atomic_write(path: Path, content: str) -> None:
    """Overwrite ``path`` with ``content`` atomically: a crash leaves the previous complete file or
    the new complete one, never a truncated one. For idempotent markers where an existing file is
    replaced, not rejected (unlike ``atomic_exclusive_write``)."""
    tmp = _temp_path(path)
    _fsync_write(tmp, content)
    tmp.replace(path)
