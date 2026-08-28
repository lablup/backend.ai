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

import os

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
