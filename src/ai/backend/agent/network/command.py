"""One way to run a privileged command, so every one of them can be given up on.

The privnet runs `ip`, `iptables` and `nsenter` under a node-wide barrier: one invocation that
never returns stops every attach, teardown and peer update on the host. Each caller used to spawn
and await its own subprocess, so each was a separate opportunity to forget the deadline -- and
three of them had.

Two guarantees, both of which need the process handle and so cannot live in the callers:

- a command past its deadline is killed and reaped, rather than left running against a host whose
  lock has since been given to somebody else;
- the same happens when the caller is cancelled from outside, which is how a request deadline or a
  shutdown reaches a command already in flight.
"""

from __future__ import annotations

import asyncio
import contextlib
from collections.abc import Sequence
from typing import Final

#: How long one privileged command may take. Generous next to what these normally do
#: (milliseconds), and finite because they run under a node-wide barrier.
DEFAULT_TIMEOUT_SEC: Final = 30.0


class CommandTimeout(Exception):
    """The command was killed for running past its deadline."""


async def run(argv: Sequence[str], *, capture_stderr: bool = True) -> tuple[int, bytes, bytes]:
    """Run ``argv`` to completion, or kill it. Returns ``(returncode, stdout, stderr)``.

    Raises `CommandTimeout` when `DEFAULT_TIMEOUT_SEC` passes. Callers turn that into their own
    error type, because what a timed-out command means differs: for a teardown it is work still
    owed, for a read it is an answer this node does not have.

    One deadline for every caller, and no per-call override: a caller that needs a shorter one
    wraps this in `asyncio.timeout`, which arrives here as a cancellation and kills the command
    exactly as the internal deadline does. The constant is read at CALL time, so a test can move
    it -- a default argument would freeze it at import.
    """
    timeout = DEFAULT_TIMEOUT_SEC
    proc = await asyncio.create_subprocess_exec(
        *argv,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE if capture_stderr else asyncio.subprocess.DEVNULL,
    )
    try:
        async with asyncio.timeout(timeout):
            out, err = await proc.communicate()
    except TimeoutError as e:
        await _kill(proc)
        raise CommandTimeout(f"command timed out after {timeout:.0f}s") from e
    except BaseException:
        # Cancelled from outside -- a request deadline, a shutdown. The command is still running
        # against the host, and the lock that authorised it is about to be given to someone else.
        await _kill(proc)
        raise
    return proc.returncode or 0, out or b"", err or b""


async def _kill(proc: asyncio.subprocess.Process) -> None:
    """End the command and reap it.

    SIGKILL rather than SIGTERM: these are `ip`, `iptables` and `nsenter`, which have nothing to
    clean up, and one already stuck on a lock is unlikely to act on a catchable signal.
    """
    with contextlib.suppress(ProcessLookupError):
        proc.kill()
    with contextlib.suppress(Exception):
        await proc.wait()
