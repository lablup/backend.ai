from __future__ import annotations

import asyncio
import ctypes
import ctypes.util
import os
import shutil
import subprocess
import sys
import time
from collections.abc import Iterator
from concurrent.futures import ProcessPoolExecutor
from unittest.mock import MagicMock, patch

import psutil
import pytest

from ai.backend.common.netns import setns


class TestSetns:
    """Tests for setns() return value checking."""

    def test_setns_raises_on_failure(self) -> None:
        """Verify setns() raises OSError when libc.setns() returns -1."""
        mock_libc = MagicMock()
        mock_libc.setns.return_value = -1

        with (
            patch("ai.backend.common.netns._get_libc", return_value=mock_libc),
            patch("ctypes.get_errno", return_value=1),
            pytest.raises(OSError, match="setns\\(\\) failed"),
        ):
            setns(42)

    def test_setns_succeeds_on_zero_return(self) -> None:
        """Verify setns() does not raise when libc.setns() returns 0."""
        mock_libc = MagicMock()
        mock_libc.setns.return_value = 0

        with patch("ai.backend.common.netns._get_libc", return_value=mock_libc):
            setns(42)

        mock_libc.setns.assert_called_once()


def _read_host_counters() -> tuple[int, int]:
    """Read network counters from the host namespace (no setns)."""
    stats = psutil.net_io_counters()
    return (stats.bytes_recv, stats.bytes_sent)


def _read_counters_after_valid_setns(pid: int) -> tuple[int, int]:
    """Enter a different netns via valid fd, read counters, then restore."""
    libc = ctypes.CDLL(ctypes.util.find_library("c"), use_errno=True)
    CLONE_NEWNET = 1 << 30
    self_ns = os.open("/proc/self/ns/net", os.O_RDONLY)
    new_ns = os.open(f"/proc/{pid}/ns/net", os.O_RDONLY)
    try:
        ret = libc.setns(new_ns, CLONE_NEWNET)
        if ret == -1:
            errno = ctypes.get_errno()
            raise OSError(errno, f"setns() failed: {os.strerror(errno)}")
        stats = psutil.net_io_counters()
        result = (stats.bytes_recv, stats.bytes_sent)
        libc.setns(self_ns, CLONE_NEWNET)
        return result
    finally:
        os.close(new_ns)
        os.close(self_ns)


def _read_counters_after_invalid_setns() -> tuple[int, int]:
    """Attempt setns with invalid fd (-1). Fails silently, stays in host namespace."""
    libc = ctypes.CDLL(ctypes.util.find_library("c"), use_errno=True)
    CLONE_NEWNET = 1 << 30
    ret = libc.setns(-1, CLONE_NEWNET)
    assert ret == -1
    stats = psutil.net_io_counters()
    return (stats.bytes_recv, stats.bytes_sent)


@pytest.mark.skipif(sys.platform != "linux", reason="Network namespaces require Linux")
@pytest.mark.skipif(not shutil.which("unshare"), reason="unshare command not found")
class TestSetnsNamespaceIsolation:
    """Verify that failed setns() causes psutil to read host-level counters.

    Uses ``unshare --net`` to create an isolated network namespace without
    requiring Docker.
    """

    @pytest.fixture
    def netns_process(self) -> Iterator[subprocess.Popen[bytes]]:
        """Spawn a sleep process in a new network namespace via unshare."""
        proc = subprocess.Popen(
            ["unshare", "--net", "sleep", "30"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        time.sleep(0.3)
        try:
            yield proc
        finally:
            proc.terminate()
            proc.wait()

    async def test_failed_setns_reads_host_counters(
        self, netns_process: subprocess.Popen[bytes]
    ) -> None:
        """When setns() fails and the return value is not checked,
        psutil reads host namespace counters instead of the isolated namespace's."""
        pid = netns_process.pid
        loop = asyncio.get_event_loop()

        with ProcessPoolExecutor(max_workers=1) as pool:
            host_rx, host_tx = await loop.run_in_executor(pool, _read_host_counters)
        with ProcessPoolExecutor(max_workers=1) as pool:
            ns_rx, ns_tx = await loop.run_in_executor(pool, _read_counters_after_valid_setns, pid)
        with ProcessPoolExecutor(max_workers=1) as pool:
            failed_rx, failed_tx = await loop.run_in_executor(
                pool, _read_counters_after_invalid_setns
            )

        # A freshly created network namespace has zero traffic.
        # Host has accumulated traffic across all interfaces.
        assert host_rx + host_tx > ns_rx + ns_tx, (
            "Host counters should be larger than isolated namespace counters"
        )
        # After failed setns, we remain in the host namespace —
        # this is the root cause of the stat spike bug.
        assert failed_rx + failed_tx > ns_rx + ns_tx, (
            "Failed setns should read host-level counters, not namespace counters"
        )
