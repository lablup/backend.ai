import asyncio
from dataclasses import dataclass
import enum
from typing import Dict, Iterable, Protocol


class ProbeStatus(enum.StrEnum):
    """
    ProbeStatus is a status of a probe check.
    """

    SUCCESS = "success"
    FAILURE = "failure"
    Timeout = "timeout"


@dataclass
class ProbeResult:
    """
    ProbeResult is a result of a probe check.
    """

    status: ProbeStatus
    message: str


class Probe(Protocol):
    """
    Probe is a component that checks the health of a system.
    """

    async def check(self, timeout: int) -> ProbeResult: ...


class Reporter(Protocol):
    """
    Reporter is a component that reports the health of a system.
    """

    async def report(self, result: ProbeResult) -> None: ...


class ProbeMonitor:
    """
    ProbeMonitor is a component that runs probes and reports the results.

    It runs the probe check at a regular interval and reports the result if the
    threshold is reached.
    """

    def __init__(self, probe: Probe, reporter: Reporter, timeout: int, interval: float, threshold: int):
        self._probe = probe
        self._reporter = reporter
        self._timeout = timeout
        self._interval = interval
        self._threshold = threshold
        self._running = True

    async def start(self) -> None:
        results = []
        while self._running:
            result = await self._probe.check(self._timeout)
            if result.status == ProbeStatus.SUCCESS:
                results.append(result)
            else:
                results = []
            if len(results) >= self._threshold:
                await self._reporter.report(result)
            await asyncio.sleep(self._interval)

    def stop(self) -> None:
        self._running = False


class ProbeMonitorManager:
    """
    ProbeMonitorManager is a component that manages multiple ProbeMonitors.

    It registers and deregisters ProbeMonitors and starts and stops them.
    """

    _loop: asyncio.AbstractEventLoop
    _lock: asyncio.Lock
    _monitors: Dict[str, ProbeMonitor]

    def __init__(self):
        self._loop = asyncio.get_running_loop()
        self._lock = asyncio.Lock()
        self._monitors = {}

    def register(self, key: str, monitor: ProbeMonitor) -> None:
        with self._lock:
            if key in self._monitors:
                return
            self._monitors[key] = monitor
        self._loop.create_task(monitor.start())

    def deregister(self, key: str) -> None:
        with self._lock:
            monitor = self._monitors.get(key)
            if monitor:
                monitor.stop()
                del self._monitors[key]
