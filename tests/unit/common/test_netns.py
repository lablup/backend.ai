from __future__ import annotations

import asyncio
import ctypes
import ctypes.util
import os
import secrets
import sys
from collections.abc import AsyncIterator
from concurrent.futures import ProcessPoolExecutor
from typing import Any
from unittest.mock import MagicMock, patch

import aiodocker
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
    """Enter container netns via valid fd, read counters, then restore."""
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
class TestSetnsNamespaceIsolation:
    """Verify that failed setns() causes psutil to read host-level counters."""

    @pytest.fixture
    async def docker(self) -> AsyncIterator[aiodocker.Docker]:
        docker = aiodocker.Docker()
        try:
            yield docker
        finally:
            await docker.close()

    @pytest.fixture
    async def running_container(self, docker: aiodocker.Docker) -> AsyncIterator[dict[str, Any]]:
        name = f"test-netns-{secrets.token_urlsafe(4)}"
        container = await docker.containers.create_or_replace(
            config={"Image": "alpine:3.8", "Cmd": ["sleep", "60"]},
            name=name,
        )
        await container.start()
        info = await container.show()
        try:
            yield info
        finally:
            await container.delete(force=True)

    async def test_failed_setns_reads_host_counters(
        self, running_container: dict[str, Any]
    ) -> None:
        """When setns() fails and the return value is not checked,
        psutil reads host namespace counters instead of the container's."""
        pid = running_container["State"]["Pid"]
        loop = asyncio.get_event_loop()

        with ProcessPoolExecutor(max_workers=1) as pool:
            host_rx, host_tx = await loop.run_in_executor(pool, _read_host_counters)
        with ProcessPoolExecutor(max_workers=1) as pool:
            container_rx, container_tx = await loop.run_in_executor(
                pool, _read_counters_after_valid_setns, pid
            )
        with ProcessPoolExecutor(max_workers=1) as pool:
            failed_rx, failed_tx = await loop.run_in_executor(
                pool, _read_counters_after_invalid_setns
            )

        # A freshly started container has near-zero network traffic.
        # Host has accumulated traffic across all interfaces.
        assert host_rx + host_tx > container_rx + container_tx, (
            "Host counters should be larger than container counters"
        )
        # After failed setns, we remain in the host namespace —
        # this is the root cause of the stat spike bug.
        assert failed_rx + failed_tx > container_rx + container_tx, (
            "Failed setns should read host-level counters, not container counters"
        )
