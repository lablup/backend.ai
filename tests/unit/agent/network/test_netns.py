"""The privnet's container-netns pinning, against real namespaces (BEP-1062).

This is the module that stands between a privileged operation and the wrong namespace. Entering a
container's netns by PID is a TOCTOU: a PID is reused the moment its process dies, so a *validate
then use* would let a privileged veth/nsenter land on the host or on another container. The defence
is to pin the process identity (pidfd) and the namespace object (an fd), then validate the pin
itself — which is only worth anything if it is exercised against actual namespaces.

So these fork a child into a real, non-host network namespace and drive the real functions. The
child needs no privilege: an unprivileged process may unshare a *user* namespace and, inside it, a
network namespace. A kernel that forbids that (a hardened distro, some containers) cannot host these
tests, and they skip loudly rather than pretend to have checked something.
"""

from __future__ import annotations

import ctypes
import os
import time
from collections.abc import Iterator
from pathlib import Path

import pytest

from ai.backend.agent.network.privnet.netns import (
    NetnsError,
    NetnsPinner,
    open_container_netns,
    pidfd_alive,
)

_CLONE_NEWUSER = 0x10000000
_CLONE_NEWNET = 0x40000000


def _unshare_netns() -> int:
    """Enter a fresh user + network namespace. Returns the libc return code."""
    libc = ctypes.CDLL("libc.so.6", use_errno=True)
    return int(libc.unshare(_CLONE_NEWUSER | _CLONE_NEWNET))


def _netns_ident(pid: int) -> tuple[int, int]:
    st = Path(f"/proc/{pid}/ns/net").stat()
    return (st.st_dev, st.st_ino)


def _spawn(*, own_netns: bool) -> int:
    """Fork a child that parks forever, optionally in a network namespace of its own. Returns its
    PID once it has confirmed (over a pipe) that it is in the namespace the caller asked for."""
    ready_r, ready_w = os.pipe()
    pid = os.fork()
    if pid == 0:  # pragma: no cover - the child never returns
        os.close(ready_r)
        code = _unshare_netns() if own_netns else 0
        os.write(ready_w, b"1" if code == 0 else b"0")
        os.close(ready_w)
        while True:
            time.sleep(3600)
    os.close(ready_w)
    ok = os.read(ready_r, 1)
    os.close(ready_r)
    if ok != b"1":
        os.kill(pid, 9)
        os.waitpid(pid, 0)
        pytest.skip("this kernel does not allow an unprivileged process to unshare a netns")
    return pid


def _reap(pid: int) -> None:
    try:
        os.kill(pid, 9)
        os.waitpid(pid, 0)
    except (ProcessLookupError, ChildProcessError):
        pass


@pytest.fixture
def container_pid() -> Iterator[int]:
    """A live process in a network namespace of its own — a container, as far as this module can
    tell, since that is exactly what it checks for."""
    pid = _spawn(own_netns=True)
    try:
        yield pid
    finally:
        _reap(pid)


@pytest.fixture
def host_pid() -> Iterator[int]:
    """A live process in the *host* netns: the namespace an attach must never target."""
    pid = _spawn(own_netns=False)
    try:
        yield pid
    finally:
        _reap(pid)


class TestPinning:
    def test_it_pins_the_container_netns(self, container_pid: int) -> None:
        pinned = open_container_netns(container_pid)
        try:
            st = os.fstat(pinned.netns_fd)
            assert (st.st_dev, st.st_ino) == _netns_ident(container_pid)
            assert (st.st_dev, st.st_ino) != _netns_ident(os.getpid())  # not ours
        finally:
            pinned.close()

    def test_the_namespace_fd_survives_the_process(self, container_pid: int) -> None:
        # The point of pinning the namespace *object* rather than re-resolving /proc/<pid>/ns/net:
        # once the process dies its path is gone (and its PID is free to be reused), while the fd
        # still names the same namespace. That is what makes the CNI child immune to PID reuse.
        pinned = open_container_netns(container_pid)
        try:
            before = os.fstat(pinned.netns_fd)
            _reap(container_pid)
            assert not Path(f"/proc/{container_pid}/ns/net").exists()
            after = os.fstat(pinned.netns_fd)
            assert (after.st_dev, after.st_ino) == (before.st_dev, before.st_ino)
        finally:
            pinned.close()

    def test_the_fd_reaches_a_child_process(self, container_pid: int) -> None:
        # It is passed to a CNI plugin via pass_fds, so it must survive exec — which Python does
        # NOT give for free: it opens every fd with O_CLOEXEC (PEP 446), so the flag has to be
        # cleared explicitly. This caught that it was not.
        pinned = open_container_netns(container_pid)
        try:
            assert os.get_inheritable(pinned.netns_fd)
            assert pinned.netns_path == f"/proc/self/fd/{pinned.netns_fd}"
        finally:
            pinned.close()

    def test_close_is_safe_to_call_twice(self, container_pid: int) -> None:
        pinned = open_container_netns(container_pid)
        pinned.close()
        pinned.close()  # a double close must not take the privnet down mid-attach


class TestWhatItRefuses:
    def test_the_host_netns(self, host_pid: int) -> None:
        # The whole point. A PID that resolves to the host's namespace would put a privileged veth
        # on the node itself; no amount of losing races may select it.
        with pytest.raises(NetnsError, match="host netns"):
            open_container_netns(host_pid)

    def test_our_own_process(self) -> None:
        # The privnet runs in the host netns, so it is its own counter-example.
        with pytest.raises(NetnsError, match="host netns"):
            open_container_netns(os.getpid())

    def test_init_and_below(self) -> None:
        with pytest.raises(NetnsError):
            open_container_netns(1)
        with pytest.raises(NetnsError):
            open_container_netns(0)
        with pytest.raises(NetnsError):
            open_container_netns(-1)

    def test_a_process_that_is_already_gone(self, container_pid: int) -> None:
        _reap(container_pid)
        with pytest.raises(NetnsError, match="gone"):
            open_container_netns(container_pid)


class TestLiveness:
    def test_a_pinned_process_reads_as_alive(self, container_pid: int) -> None:
        pinned = open_container_netns(container_pid)
        try:
            assert pidfd_alive(pinned.pidfd)
        finally:
            pinned.close()

    def test_a_dead_one_does_not(self, container_pid: int) -> None:
        # This is the re-check the attach makes after resolving the PID from containerd a second
        # time: a task that exited mid-attach must be caught before the veth is wired up.
        pinned = open_container_netns(container_pid)
        try:
            _reap(container_pid)
            assert not pidfd_alive(pinned.pidfd)
        finally:
            pinned.close()


class TestThePinnerSeam:
    """What the privnet actually holds. It exists so the attach path can be driven in a test, so it
    had better be the real thing in production."""

    def test_it_pins_for_real(self, container_pid: int) -> None:
        pinner = NetnsPinner()
        pinned = pinner.open(container_pid)
        try:
            assert (
                os.fstat(pinned.netns_fd).st_ino
                == Path(f"/proc/{container_pid}/ns/net").stat().st_ino
            )
            assert pinner.alive(pinned)
        finally:
            pinned.close()

    def test_it_refuses_the_host_netns_too(self, host_pid: int) -> None:
        with pytest.raises(NetnsError):
            NetnsPinner().open(host_pid)
