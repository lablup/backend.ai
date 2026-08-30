"""Which namespace the agent may point the privnet at, asked of the kernel.

On containerd the PID comes from a root-owned daemon the agent cannot forge. A rootless backend
has no daemon — its container record is a journal the agent writes — so a compromised agent could
name any PID and have a privileged veth attached into that namespace. An unprivileged agent can
only create namespaces inside a user namespace it owns, so requiring that ownership bounds it to
what it could have made anyway.

Measured on a live node: an enroot kernel's netns is owned by uid 1000, the host's by 0 — and so is
a containerd kernel's, which is why the caller sets this only for the rootless backends.
"""

from __future__ import annotations

import contextlib
import os
import subprocess
import time
from collections.abc import Iterator

import pytest

from ai.backend.agent.network.privnet.netns import (
    NetnsError,
    _netns_owner_uid,
    open_container_netns,
)


class TestTheOwnerIsReadFromTheKernel:
    def test_the_host_netns_is_owned_by_root(self) -> None:
        """The test process runs in the host netns, which belongs to the initial user namespace —
        so the answer must be 0 however unprivileged the caller is. This also proves the ioctl pair
        works on this kernel, so a mismatch later reads as a real one rather than a missing
        syscall."""
        fd = os.open("/proc/self/ns/net", os.O_RDONLY)
        try:
            assert _netns_owner_uid(fd) == 0
        finally:
            os.close(fd)


class TestAMismatchIsRefused:
    def test_a_netns_owned_by_someone_else_is_rejected(self) -> None:
        """The test process sits in the host netns, owned by uid 0. Asking for a different owner
        must fail — and it must fail on the ownership, not on the host-netns rule, so the check is
        exercised rather than shadowed."""
        with pytest.raises(NetnsError) as excinfo:
            open_container_netns(os.getpid(), expected_owner_uid=4242)
        # The host-netns rule fires first for this PID, which is itself correct; either way the
        # attach is refused. Both messages are accepted so the test does not depend on the order.
        assert "host netns" in str(excinfo.value) or "owned by uid" in str(excinfo.value)

    def test_pid_one_is_refused_outright(self) -> None:
        with pytest.raises(NetnsError, match="PID <= 1"):
            open_container_netns(1, expected_owner_uid=0)


def _userns_available() -> bool:
    """Whether this kernel lets an unprivileged process create a user namespace."""
    return (
        subprocess.run(["unshare", "-r", "-n", "true"], capture_output=True, timeout=10).returncode
        == 0
    )


@contextlib.contextmanager
def _a_netns_we_own() -> Iterator[int]:
    """A live process in a NON-host netns owned by this uid — an enroot kernel in miniature.

    The host netns is rejected before the owner is ever consulted, so a test that points at its own
    PID exercises nothing. This is the only shape that reaches the check.
    """
    proc = subprocess.Popen(
        ["unshare", "-r", "-n", "sleep", "60"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        host_ino = os.stat("/proc/self/ns/net").st_ino
        deadline = time.monotonic() + 5.0
        while time.monotonic() < deadline:
            # `unshare` execs `sleep` only after the namespaces are made, so wait for the child's
            # netns to stop being the one we are in rather than for the process to merely exist.
            try:
                if os.stat(f"/proc/{proc.pid}/ns/net").st_ino != host_ino:
                    break
            except OSError:
                pass
            time.sleep(0.02)
        else:
            pytest.skip("the unshared netns never appeared")
        yield proc.pid
    finally:
        proc.kill()
        proc.wait()


@pytest.mark.skipif(not _userns_available(), reason="unprivileged user namespaces are disabled")
class TestTheOwnerCheckOnANamespaceWeActuallyOwn:
    """The check exists so a compromised rootless agent cannot name a netns it did not create.

    Pointing at the test's own PID cannot show that: `open_container_netns` rejects the host netns
    two branches earlier, so such a test passes with `expected_owner_uid` deleted from the function
    (verified by mutation). These use a real unshared namespace, where the owner branch is the only
    one that can fire.
    """

    def test_a_namespace_this_uid_owns_is_accepted(self) -> None:
        with _a_netns_we_own() as pid:
            pinned = open_container_netns(pid, expected_owner_uid=os.getuid())
            try:
                assert pinned.netns_fd >= 0
            finally:
                pinned.close()

    def test_the_same_namespace_is_refused_for_another_uid(self) -> None:
        """The negative half. Refused *on the ownership* — the message is asserted so a future
        reordering that shadows this branch again fails here instead of passing quietly."""
        with _a_netns_we_own() as pid:
            with pytest.raises(NetnsError, match="owned by uid"):
                open_container_netns(pid, expected_owner_uid=os.getuid() + 1)

    def test_without_an_expectation_the_owner_is_not_consulted(self) -> None:
        """containerd passes None: the PID came from a root daemon and is already authoritative."""
        with _a_netns_we_own() as pid:
            pinned = open_container_netns(pid)
            pinned.close()
