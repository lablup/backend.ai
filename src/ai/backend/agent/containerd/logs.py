"""Rotate container logs the way Docker's log driver does.

The Docker backend configures dockerd's `local` driver with max-size and max-file, which gives each
kernel a fixed set of log files: an active one plus a few rotated ones, with the oldest deleted once
there are more than max-file. The kernel's log is a sliding window of the last (max-size x max-file)
bytes, and everything older is gone. That is not a compromise we are introducing here — it is what
`docker logs` already returns for these kernels today.

The containerd shim does none of this. It opens the path we gave it at container start and appends
to it for the container's whole life, so one talkative long-running kernel could fill the disk. This
module gives containerd the same window Docker has: same file layout, same per-file size, same file
count, same drop-the-oldest behaviour.

The one thing we cannot copy is *how* the rotation happens. Docker's driver owns the write end of
the container's stdout, so it rotates by simply starting a new file. The shim owns ours and holds
that fd for the container's whole life — renaming the active file would leave it appending to an
orphaned inode, and every subsequent line would go somewhere nobody can read. So the active file is
rotated in place: its contents are copied out to `.1`, and it is truncated to zero underneath the
writer. The shim's fd is O_APPEND, so its next write lands at the (new) end of file and the log
continues seamlessly.

That leaves one gap Docker does not have: a line the shim appends between the copy and the truncate
is dropped. The window is a single read/truncate pair. Closing it would mean owning the write end —
handing the shim a FIFO and reading it ourselves — and then an agent that is restarting or wedged
blocks the container's stdout and hangs the kernel. Kernels are meant to survive an agent restart,
so that trade is not available to us.
"""

from __future__ import annotations

import logging
import os
import shlex
import sys
from pathlib import Path
from urllib.parse import urlencode

# The writer owns the layout (it is the one that creates these files); import it rather than
# restating it, so the reader and the writer cannot drift apart on how a log is laid out.
from ai.backend.agent.containerd import log_writer
from ai.backend.agent.containerd.log_writer import (
    LOG_FILE_COUNT,
    rotated_path,
)
from ai.backend.logging import BraceStyleAdapter

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


def rotated_paths(active: Path) -> list[Path]:
    """Every file that belongs to this log, newest first: the active one, then .1, .2, ..."""
    return [active, *(rotated_path(active, i) for i in range(1, LOG_FILE_COUNT))]


def unlink_log_files(active: Path) -> None:
    """Remove the whole set. The rotated files are as much this kernel's log as the active one."""
    for path in rotated_paths(active):
        path.unlink(missing_ok=True)


def read_log_tail(active: Path, max_bytes: int) -> bytes:
    """The last ``max_bytes`` of the log, oldest rotated file through to the active one.

    Docker's `container.log()` reads across the rotated files the same way; reading only the active
    file would return whatever happens to be left since the last rotation, which for a freshly
    rotated log is almost nothing.
    """
    chunks: list[bytes] = []
    remaining = max_bytes
    # Walk newest -> oldest, taking the tail of each, and stop once we have enough.
    for path in rotated_paths(active):
        if remaining <= 0:
            break
        try:
            with path.open("rb") as f:
                size = f.seek(0, os.SEEK_END)
                take = min(size, remaining)
                f.seek(size - take, os.SEEK_SET)
                chunks.append(f.read(take))
                remaining -= take
        except FileNotFoundError:
            continue  # this log has not rotated that far yet
        except OSError as e:
            log.warning("cannot read container log {}: {!r}", path, e)
            continue
    return b"".join(reversed(chunks))


def write_logger_launcher(path: Path) -> Path:
    """Write the executable the shim starts for `binary://` logging, and return it.

    containerd execs the URI's path directly, so it has to be a real executable. Rather than ship a
    compiled binary, pin the running agent's own interpreter and import path into a two-line shell
    script — that way the logger is the same code, from the same tree, as the agent that wrote it.
    """
    # By PATH, not as a module: running `-m ai.backend.agent.containerd.log_writer` would execute
    # the package __init__, which imports the whole agent — turning every container's logger into a
    # second copy of the agent, and any import error in the agent into a container that cannot
    # start. The writer is standard-library-only precisely so it can be run bare.
    writer = Path(log_writer.__file__).resolve()
    launcher = f'#!/bin/sh\nexec {shlex.quote(sys.executable)} {shlex.quote(str(writer))} "$@"\n'
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(launcher)
    path.chmod(0o755)
    return path


def logger_uri(launcher: Path, log_root: Path, max_total_bytes: int) -> str:
    """The `binary://` URI handed to containerd as the task's stdout/stderr.

    The query pairs are flattened into the logger's argv by containerd, which is why they are named
    like the command-line flags they become.
    """
    query = urlencode({"--log-root": str(log_root), "--max-length": str(max_total_bytes)})
    return f"binary://{launcher}?{query}"
