from ..testcases.testcases import TestSpec
from .exporter import TestExporter


class TestRunner:
    _spec: TestSpec
    _exporter: TestExporter

    def __init__(self, spec: TestSpec, exporter: TestExporter) -> None:
        self._spec = spec
        self._exporter = exporter

    async def run(self) -> None:
        try:
            await self._spec.run_test()
            await self._exporter.export_done(self._spec)
        except BaseException as e:
            await self._exporter.export_exception(self._spec, e)
