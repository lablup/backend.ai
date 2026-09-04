"""Race-free container network-namespace handles for the privnet (BEP-1062).

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
the privnet's own netns, since the privnet runs in the host netns). The caller resolves
the PID from containerd (authoritative) and re-checks it against the pidfd, so the only
way to be redirected is to lose several races at once *and* land on another managed
container — and even then the host netns can never be selected.
"""

from __future__ import annotations

import ctypes
import os
from dataclasses import dataclass
from functools import cache
from pathlib import Path

# os.pidfd_open (Python 3.9+, Linux 5.3+) is compiled into the ``os`` module only when the
# interpreter's build detected it (HAVE_PIDFD_OPEN). Some portable CPython builds -- notably
# python-build-standalone, as shipped by uv -- are built against older kernel headers and omit
# it, so it must be treated as optional. When absent, open_container_netns falls back to a
# signal-0 liveness probe (see there) instead of hard-failing the whole privnet.
_HAS_PIDFD_OPEN = hasattr(os, "pidfd_open")


# ioctls on a namespace fd (linux/nsfs.h). NS_GET_USERNS yields the user namespace that owns the
# namespace; NS_GET_OWNER_UID reads that user namespace's owner. Both are _IO (the owner uid comes
# back through the pointer argument, which is why it is NOT _IOR).
_NS_GET_USERNS = 0xB701
_NS_GET_OWNER_UID = 0xB704


class NetnsError(RuntimeError):
    """The target PID is gone, was recycled, or resolves to the host netns."""


@dataclass(frozen=True)
class _NsIdent:
    st_dev: int
    st_ino: int


@cache
def _host_netns_ident() -> _NsIdent:
    """Identity of the netns the privnet itself runs in. The privnet always runs in the
    host netns, so this is exactly the namespace an attach must never target."""
    st = Path("/proc/self/ns/net").stat()
    return _NsIdent(st.st_dev, st.st_ino)


@dataclass
class PinnedNetns:
    """A container netns pinned by fd plus the pidfd that pins the owning process.
    Use ``netns_path`` as the CNI ``CNI_NETNS`` and pass ``netns_fd`` to the child via
    ``pass_fds``. Always ``close()`` in a finally block.

    ``pidfd`` is -1 when the interpreter lacks ``os.pidfd_open`` (see open_container_netns);
    ``pid`` is then used for the liveness re-check instead of the pidfd."""

    netns_fd: int
    pidfd: int
    pid: int

    @property
    def netns_path(self) -> str:
        # Resolves inside the (fd-inheriting) child to the pinned namespace object,
        # immune to PID reuse.
        return f"/proc/self/fd/{self.netns_fd}"

    def close(self) -> None:
        for fd in (self.netns_fd, self.pidfd):
            if fd < 0:
                continue  # no pidfd was opened (fallback build)
            try:
                os.close(fd)
            except OSError:
                pass


def _netns_owner_uid(netns_fd: int) -> int:
    """The uid that owns the user namespace this netns belongs to.

    Answered by the kernel, which is the point: everything else about a container reaches the
    privnet through the agent, and this does not.
    """
    libc = ctypes.CDLL("libc.so.6", use_errno=True)
    userns_fd = libc.ioctl(netns_fd, _NS_GET_USERNS)
    if userns_fd < 0:
        raise NetnsError(f"cannot read the netns owner: {os.strerror(ctypes.get_errno())}")
    try:
        uid = ctypes.c_uint32()
        if libc.ioctl(userns_fd, _NS_GET_OWNER_UID, ctypes.byref(uid)) < 0:
            raise NetnsError(f"cannot read the netns owner uid: {os.strerror(ctypes.get_errno())}")
        return uid.value
    finally:
        os.close(userns_fd)


def open_container_netns(pid: int, *, expected_owner_uid: int | None = None) -> PinnedNetns:
    """Pin ``pid`` and its network namespace, rejecting the host netns.

    Raises NetnsError if the PID is invalid/exited or its netns is the host's. The
    returned ``netns_fd`` is inheritable (no CLOEXEC) so a CNI child can receive it via
    ``pass_fds``; the caller owns both fds and must ``close()`` them.

    When the interpreter lacks ``os.pidfd_open`` (some portable CPython builds), the pidfd
    guarantee is unavailable: the process identity is confirmed with a signal-0 probe instead
    and ``pidfd`` is -1. That loses PID-reuse pinning; the netns fd, the host-netns rejection
    below, and the caller's containerd PID re-resolution still hold.
    """
    if pid <= 1:
        raise NetnsError("refusing PID <= 1 (host/init)")
    pidfd = -1
    if _HAS_PIDFD_OPEN:
        try:
            pidfd = os.pidfd_open(pid)
        except (ProcessLookupError, OSError) as e:
            raise NetnsError("target process is gone") from e
    else:
        try:
            os.kill(pid, 0)
        except ProcessLookupError as e:
            raise NetnsError("target process is gone") from e
        except PermissionError:
            pass  # the process exists but is owned by another uid -- still alive
    try:
        netns_fd = os.open(f"/proc/{pid}/ns/net", os.O_RDONLY)
    except OSError as e:
        if pidfd >= 0:
            os.close(pidfd)
        raise NetnsError("cannot open container netns") from e
    # Python opens every fd with O_CLOEXEC (PEP 446), so it must be cleared explicitly: the fd has
    # to survive exec to reach a CNI child through ``pass_fds``, which is the whole point of
    # handing that child ``netns_path`` instead of a /proc path it could re-resolve.
    os.set_inheritable(netns_fd, True)
    st = os.fstat(netns_fd)
    if _NsIdent(st.st_dev, st.st_ino) == _host_netns_ident():
        os.close(netns_fd)
        if pidfd >= 0:
            os.close(pidfd)
        raise NetnsError("target resolves to the host netns")
    if expected_owner_uid is not None:
        # Which netns the agent may point us at, asked of the kernel rather than of the agent.
        #
        # It matters only where the PID is not authoritative. On containerd the PID comes from the
        # daemon, which runs as root and the agent cannot forge; on a rootless backend the record
        # is written by the agent itself, so a compromised agent could name any PID and have a
        # privileged veth attached into that namespace. An unprivileged agent can only ever create
        # namespaces inside a user namespace it owns, so requiring that ownership bounds it to
        # exactly what it could have made anyway. (Measured: an enroot kernel's netns is owned by
        # uid 1000, the host's by 0 — as is a containerd kernel's, which is why the caller only
        # sets this for the rootless backends.)
        try:
            owner = _netns_owner_uid(netns_fd)
        except NetnsError:
            os.close(netns_fd)
            if pidfd >= 0:
                os.close(pidfd)
            raise
        if owner != expected_owner_uid:
            os.close(netns_fd)
            if pidfd >= 0:
                os.close(pidfd)
            raise NetnsError(
                f"netns is owned by uid {owner}, not the agent's ({expected_owner_uid})"
            )
    return PinnedNetns(netns_fd=netns_fd, pidfd=pidfd, pid=pid)


class NetnsPinner:
    """The seam the privnet pins namespaces through.

    Production always uses this one — it is a thin pass-through to the functions above. It exists so
    the attach path can be driven in a test without a real container: pinning needs a live process
    in a non-host netns, which a unit test has no way to produce, and without the seam every test of
    what attach *does* would have to stop at the pin.
    """

    def open(self, pid: int, *, expected_owner_uid: int | None = None) -> PinnedNetns:
        return open_container_netns(pid, expected_owner_uid=expected_owner_uid)

    def alive(self, pinned: PinnedNetns) -> bool:
        if pinned.pidfd < 0:
            # No pidfd (fallback build): probe the pid. Weaker than the pidfd identity check
            # (a recycled PID would read as alive), but the caller re-resolves the PID from
            # containerd, which is the authoritative identity check.
            try:
                os.kill(pinned.pid, 0)
            except ProcessLookupError:
                return False
            except PermissionError:
                return True
            return True
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
