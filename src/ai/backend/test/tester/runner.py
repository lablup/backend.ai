import uuid

from ..contexts.tester import TestIDContext
from ..testcases.spec_manager import TestSpec
from .exporter import TestExporter


class TestRunner:
    _spec: TestSpec
    _exporter: TestExporter

    def __init__(self, spec: TestSpec, exporter: TestExporter) -> None:
        self._spec = spec
        self._exporter = exporter

    async def run(self) -> None:
        with TestIDContext.with_current(uuid.uuid4()):
            await self._exporter.export_start(self._spec.name)
            try:
                await self._spec.template.run_test(self._exporter)
                await self._exporter.export_done(self._spec.name)
            except BaseException as e:
                await self._exporter.export_exception(self._spec.name, e)
