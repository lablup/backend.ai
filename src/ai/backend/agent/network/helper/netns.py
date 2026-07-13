"""Race-free container network-namespace handles for the helper (BEP-1062).

The dangerous operation is entering a container's network namespace by PID: a PID is
reused the moment its process dies, so *validate PID -> then use PID* is a classic
TOCTOU that can redirect a privileged op at the host or another container's netns.

This module closes that window with two kernel primitives instead of re-reading
``/proc`` by path repeatedly:

1. ``pidfd_open(pid)`` pins the *process identity*. Once held, the pidfd never refers
   to a different process even if the PID is recycled; operations fail if it exited.
2. The netns is opened once into an **fd** that pins the *namespace object*. All later
   use (passing ``/proc/self/fd/<n>`` to a CNI plugin) refers to that same pinned
   object, never a path that could be re-resolved to a different namespace.

Validation then happens on the pinned fd itself: reject the host netns (identified by
the helper's own netns, since the helper runs in the host netns). The caller resolves
the PID from containerd (authoritative) and re-checks it against the pidfd, so the only
way to be redirected is to lose several races at once *and* land on another managed
container — and even then the host netns can never be selected.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import cache
from pathlib import Path


class NetnsError(RuntimeError):
    """The target PID is gone, was recycled, or resolves to the host netns."""


@dataclass(frozen=True)
class _NsIdent:
    st_dev: int
    st_ino: int


@cache
def _host_netns_ident() -> _NsIdent:
    """Identity of the netns the helper itself runs in. The helper always runs in the
    host netns, so this is exactly the namespace an attach must never target."""
    st = Path("/proc/self/ns/net").stat()
    return _NsIdent(st.st_dev, st.st_ino)


@dataclass
class PinnedNetns:
    """A container netns pinned by fd plus the pidfd that pins the owning process.
    Use ``netns_path`` as the CNI ``CNI_NETNS`` and pass ``netns_fd`` to the child via
    ``pass_fds``. Always ``close()`` in a finally block."""

    netns_fd: int
    pidfd: int

    @property
    def netns_path(self) -> str:
        # Resolves inside the (fd-inheriting) child to the pinned namespace object,
        # immune to PID reuse.
        return f"/proc/self/fd/{self.netns_fd}"

    def close(self) -> None:
        for fd in (self.netns_fd, self.pidfd):
            try:
                os.close(fd)
            except OSError:
                pass


def open_container_netns(pid: int) -> PinnedNetns:
    """Pin ``pid`` and its network namespace, rejecting the host netns.

    Raises NetnsError if the PID is invalid/exited or its netns is the host's. The
    returned ``netns_fd`` is inheritable (no CLOEXEC) so a CNI child can receive it via
    ``pass_fds``; the caller owns both fds and must ``close()`` them.
    """
    if pid <= 1:
        raise NetnsError("refusing PID <= 1 (host/init)")
    try:
        pidfd = os.pidfd_open(pid)
    except (ProcessLookupError, OSError) as e:
        raise NetnsError("target process is gone") from e
    try:
        netns_fd = os.open(f"/proc/{pid}/ns/net", os.O_RDONLY)
    except OSError as e:
        os.close(pidfd)
        raise NetnsError("cannot open container netns") from e
    # Python opens every fd with O_CLOEXEC (PEP 446), so it must be cleared explicitly: the fd has
    # to survive exec to reach a CNI child through ``pass_fds``, which is the whole point of
    # handing that child ``netns_path`` instead of a /proc path it could re-resolve.
    os.set_inheritable(netns_fd, True)
    st = os.fstat(netns_fd)
    if _NsIdent(st.st_dev, st.st_ino) == _host_netns_ident():
        os.close(netns_fd)
        os.close(pidfd)
        raise NetnsError("target resolves to the host netns")
    return PinnedNetns(netns_fd=netns_fd, pidfd=pidfd)


class NetnsPinner:
    """The seam the helper pins namespaces through.

    Production always uses this one — it is a thin pass-through to the functions above. It exists so
    the attach path can be driven in a test without a real container: pinning needs a live process
    in a non-host netns, which a unit test has no way to produce, and without the seam every test of
    what attach *does* would have to stop at the pin.
    """

    def open(self, pid: int) -> PinnedNetns:
        return open_container_netns(pid)

    def alive(self, pinned: PinnedNetns) -> bool:
        return pidfd_alive(pinned.pidfd)


def pidfd_alive(pidfd: int) -> bool:
    """True if the pinned process is still alive (used to re-confirm identity after
    resolving the PID from containerd a second time).

    A pidfd becomes readable (POLLIN) only once the process has exited; while it is
    still running a zero-timeout poll returns no events.
    """
    import select

    poller = select.poll()
    poller.register(pidfd, select.POLLIN)
    return len(poller.poll(0)) == 0
