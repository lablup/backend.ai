"""A minimal PID 1 for kernel containers — the job Docker's ``--init`` (tini) does for us.

Why this exists
---------------
A process that dies is not gone until its parent calls wait(); until then it is a zombie holding a
PID. When a parent dies first, its children are re-parented to PID 1, so PID 1 must keep reaping
processes that were never its own. Normally an init does that. Inside a container, whatever we run
IS PID 1 — and the kernel runner does not reap.

The Docker backend sets ``HostConfig.Init: True``, so dockerd puts its bundled tini at PID 1 and we
get this for free. containerd has no such thing: we build the OCI spec ourselves, runc injects no
init, and the kernel runner ends up as PID 1 with nobody reaping orphans. A long-lived session whose
workload forks grandchildren (shell loops, build tools, backgrounded daemons) then accumulates
zombies until it runs out of PIDs.

Why a separate process, and not just reaping inside the runner
--------------------------------------------------------------
The runner drives user code through ``asyncio.create_subprocess_exec``, and asyncio reaps the
children it spawned itself (waitpid on a specific pid). A blanket ``waitpid(-1)`` in the same
process would race it and steal those exit statuses, so the runner would lose the exit code of the
very code it was asked to run. tini avoids this by taking PID 1 and forking the real program as its
child — so we do the same, and the runner keeps its own children.

Why Python, and not a tini binary
---------------------------------
tini is a static C binary and would need a build per architecture. The kernel runner's interpreter
is already bind-mounted into every kernel at /opt/backend.ai/bin/python, so this costs no new
artifact, no build-pipeline change, and no per-arch packaging — just one more small process.
"""

import ctypes
import ctypes.util
import os
import signal
import sys

# prctl(PR_SET_CHILD_SUBREAPER, 1): make orphaned descendants re-parent to US rather than to PID 1.
# As PID 1 this changes nothing — orphans already land here. It matters when we are not PID 1
# (which is also what makes the reaping testable without a PID namespace), and it is what tini's
# -s flag does.
_PR_SET_CHILD_SUBREAPER = 36

# Signals a supervisor is expected to pass down rather than act on itself.
_FORWARDED = (
    signal.SIGTERM,
    signal.SIGINT,
    signal.SIGHUP,
    signal.SIGQUIT,
    signal.SIGUSR1,
    signal.SIGUSR2,
)


def _become_subreaper() -> None:
    try:
        libc = ctypes.CDLL(ctypes.util.find_library("c"), use_errno=True)
        libc.prctl(_PR_SET_CHILD_SUBREAPER, 1, 0, 0, 0)
    except (OSError, AttributeError):
        # Not Linux, or no libc to talk to. As PID 1 we reap orphans anyway; this was only ever
        # belt-and-braces for the case where we are not.
        pass


def main(argv: list[str]) -> int:
    if not argv:
        print("usage: init.py <command> [args...]", file=sys.stderr)
        return 2

    _become_subreaper()

    child_pid = os.fork()
    if child_pid == 0:
        # The real program. It runs as a child, so its own subprocess handling (asyncio's
        # per-pid waitpid) is untouched by the reaping we do below.
        os.execvp(argv[0], argv)

    def _forward(signum: int, _frame: object) -> None:
        try:
            os.kill(child_pid, signum)
        except ProcessLookupError:
            pass  # the child is already gone; the wait loop below is about to notice

    for sig in _FORWARDED:
        signal.signal(sig, _forward)

    # Reap everything, not just our own child: orphans of the workload are re-parented to us, and
    # nobody else will collect them. Keep going until the real program itself exits — any orphans
    # still alive at that point die with the container's PID namespace.
    while True:
        try:
            pid, status = os.wait()
        except ChildProcessError:
            # No children at all. The child must already have been reaped; nothing left to wait on.
            return 0
        except InterruptedError:  # pragma: no cover - PEP 475 normally retries for us
            continue
        if pid != child_pid:
            continue  # an orphan; reaped, and that is all it needed
        if os.WIFSIGNALED(status):
            # Report it the way a shell would, so the exit code still says which signal it was.
            return 128 + os.WTERMSIG(status)
        return os.WEXITSTATUS(status)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
