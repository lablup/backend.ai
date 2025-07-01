import uuid

from ai.backend.test.data.tester import TestSpecMeta

from ..contexts.tester import TestSpecMetaContext
from ..testcases.spec_manager import TestSpec
from .exporter import TestExporter


class TestRunner:
    _spec: TestSpec
    _exporter: TestExporter

    def __init__(self, spec: TestSpec, exporter: TestExporter) -> None:
        self._spec = spec
        self._exporter = exporter

    async def run(self) -> None:
        with TestSpecMetaContext.with_current(
            TestSpecMeta(
                test_id=uuid.uuid4(),
                spec_name=self._spec.name,
            )
        ):
            await self._exporter.export_start()
            try:
                await self._spec.template.run_test(self._exporter)
                await self._exporter.export_done()
            except BaseException as e:
                await self._exporter.export_exception(e)
