from __future__ import annotations

import subprocess
import sys
import time
from collections.abc import Iterator
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import pytest

from ai.backend.agent.docker.intrinsic import netstat_ns_work


@pytest.mark.skipif(sys.platform != "linux", reason="Network namespaces require Linux")
class TestNetstatNsWork:
    """Tests for netstat_ns_work with real namespace switching."""

    @pytest.fixture
    def netns_process(self) -> Iterator[subprocess.Popen[bytes]]:
        """Spawn a sleep process in a new network namespace via unshare."""
        proc = subprocess.Popen(
            ["unshare", "--net", "sleep", "30"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        time.sleep(0.3)
        if proc.poll() is not None:
            pytest.skip("unshare --net failed (insufficient privileges)")
        try:
            yield proc
        finally:
            proc.terminate()
            proc.wait()

    def test_netstat_ns_work_reads_isolated_namespace(
        self, netns_process: subprocess.Popen[bytes]
    ) -> None:
        """netstat_ns_work should read counters from the target namespace,
        not from the host."""
        pid = netns_process.pid
        ns_path = Path(f"/proc/{pid}/ns/net")
        with ProcessPoolExecutor(max_workers=1) as pool:
            result = pool.submit(netstat_ns_work, ns_path).result()
        # A fresh network namespace only has loopback with zero counters.
        assert "lo" in result
        lo = result["lo"]
        assert lo.bytes_recv == 0
        assert lo.bytes_sent == 0

    def test_netstat_ns_work_raises_on_invalid_namespace(self) -> None:
        """netstat_ns_work should raise OSError when setns() fails
        on a non-namespace fd (e.g. /dev/null)."""
        with ProcessPoolExecutor(max_workers=1) as pool:
            future = pool.submit(netstat_ns_work, Path("/dev/null"))
            with pytest.raises(OSError):
                future.result()
