import asyncio
from dataclasses import dataclass
import enum
from typing import Iterable, Protocol


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

    async def check(self) -> ProbeResult: ...


class Reporter(Protocol):
    """
    Reporter is a component that reports the health of a system.
    """

    async def report(self, result: ProbeResult) -> None: ...


class ProbeMonitor:
    """
    ProbeMonitor is a component that runs probes and reports the results.

    It runs the probes in a loop with a given interval.
    """

    def __init__(self, probes: Iterable[Probe], reporter: Reporter, interval: float):
        self.probes = probes
        self.reporter = reporter
        self.interval = interval

    async def run(self) -> None:
        while True:
            for probe in self.probes:
                result = await probe.check()
                if result.type != ProbeStatus.SUCCESS:
                    await self.reporter.report(result)
            await asyncio.sleep(self.interval)
