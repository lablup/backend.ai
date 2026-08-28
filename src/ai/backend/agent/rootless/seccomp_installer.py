"""Harden the container, then exec the real command. Runs INSIDE the container.

    seccomp_installer.py <filter.bpf|-> <command> [args...]

``-`` for the filter means the operator chose the jail sandbox and there is nothing to install;
the IPC step still runs, which is why this is invoked unconditionally.

The agent compiles the profile (see ``seccomp.py``) and drops the packed ``struct sock_filter[]``
into the container's gate directory; this puts it on and hands over. It sits between the two-phase
pause wrapper and the kernel entrypoint, which is the only moment that works: enroot's own setup
needs mount/pivot_root and so must not be filtered, and everything the user can influence starts
after this point — the same boundary runc applies the filter at.

STANDARD LIBRARY ONLY, and no imports from the agent: this executes with the *container's*
interpreter (the mounted krunner python), which knows nothing about the agent's packages.

A filter survives execve, so the exec'd command and all of its descendants stay confined.
``PR_SET_NO_NEW_PRIVS`` is deliberately NOT set: inside a user namespace the container's root
already holds CAP_SYS_ADMIN over that namespace, which is what ``PR_SET_SECCOMP`` checks, so the
filter installs without it — and setting it would break `sudo` in the session for no gain.
"""

import ctypes
import os
import sys
from pathlib import Path

PR_SET_SECCOMP = 22
SECCOMP_MODE_FILTER = 2
_SOCK_FILTER_SIZE = 8
# From <sched.h>. os.unshare exists on 3.12+, but the constant is spelled out so this file
# keeps working against an older container interpreter.
CLONE_NEWIPC = 0x08000000


class _SockFilter(ctypes.Structure):
    _fields_ = [
        ("code", ctypes.c_uint16),
        ("jt", ctypes.c_uint8),
        ("jf", ctypes.c_uint8),
        ("k", ctypes.c_uint32),
    ]


class _SockFprog(ctypes.Structure):
    _fields_ = [
        ("len", ctypes.c_ushort),
        ("filter", ctypes.POINTER(_SockFilter)),
    ]


def install(program: bytes) -> None:
    count, remainder = divmod(len(program), _SOCK_FILTER_SIZE)
    if remainder or not count:
        raise ValueError(f"malformed BPF program: {len(program)} bytes")
    buffer = ctypes.create_string_buffer(program, len(program))
    fprog = _SockFprog(count, ctypes.cast(buffer, ctypes.POINTER(_SockFilter)))
    libc = ctypes.CDLL("libc.so.6", use_errno=True)
    if libc.prctl(PR_SET_SECCOMP, SECCOMP_MODE_FILTER, ctypes.byref(fprog), 0, 0) != 0:
        raise OSError(ctypes.get_errno(), "PR_SET_SECCOMP failed")


def unshare_ipc() -> None:
    """Give the container its own SysV IPC namespace (message queues, semaphores, shm segments).

    enroot cannot do this itself: passing `--ipc` makes its `10-devices` hook rebuild /dev, and
    that hook bind-mounts /dev/log with no `nofail`, so it hard-fails on any host without a syslog
    socket — which is every containerised agent. Without it every kernel on a node shares the
    HOST's IPC namespace (measured: two kernels and the host all report the same
    `ipc:[4026531839]`, and a segment created in one is listed by `ipcs` in the other). Docker
    gives each container its own, so this is a parity gap, not a design choice.

    Here it costs nothing: the container is already inside its user namespace, where its root holds
    CAP_SYS_ADMIN, so the unshare is permitted. Doing it after the gate also keeps it away from the
    runtime's own setup.

    Loud but not fatal, matching how the agent treats a profile it cannot load: an isolation step
    that fails should be visible, but refusing to start the kernel is the worse trade.
    """
    libc = ctypes.CDLL("libc.so.6", use_errno=True)
    if libc.unshare(CLONE_NEWIPC) != 0:
        err = ctypes.get_errno()
        sys.stderr.write(
            f"[bai] WARNING: could not unshare the IPC namespace ({os.strerror(err)}); "
            "this kernel shares SysV IPC with the rest of the node\n"
        )


def main(argv: list[str]) -> None:
    """Ends in ``execv``, which never returns — so the failure paths raise rather than return."""
    if len(argv) < 3:
        sys.stderr.write(f"usage: {argv[0]} <filter.bpf> <command> [args...]\n")
        raise SystemExit(2)
    filter_path, command = argv[1], argv[2:]
    unshare_ipc()
    if filter_path == "-":
        # Jail sandbox: no filter was generated. The IPC step above still ran.
        os.execv(command[0], command)
    program = Path(filter_path).read_bytes()
    try:
        install(program)
    except Exception as e:
        # Refuse to run unconfined. A container that silently started without the filter it was
        # supposed to have is worse than one that failed to start: nothing downstream would ever
        # notice, and the session would look exactly like a confined one.
        sys.stderr.write(f"[bai] refusing to start unconfined: seccomp install failed: {e!r}\n")
        raise SystemExit(1) from e
    # Replaces this process; it returns only by raising.
    os.execv(command[0], command)


if __name__ == "__main__":
    main(sys.argv)
