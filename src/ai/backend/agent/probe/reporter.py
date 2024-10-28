import logging
from ai.backend.agent.probe.monitor import ProbeResult
from ai.backend.logging import BraceStyleAdapter


class LogReporter:
    def __init__(self, name: str):
        self.log = BraceStyleAdapter(logging.getLogger(__name__), extra={"reporter_name": name})

    async def report(self, result: ProbeResult) -> None:
        self.log.warning(f"Probe check {result.status}: {result.message}")
