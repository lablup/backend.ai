import asyncio

from ..testcases.testcases import TestSpec, TestSpecManager, TestTag
from .exporter import TestExporter
from .runner import TestRunner

_DEFAULT_CONCURRENCY = 10


class Tester:
    _spec_manager: TestSpecManager
    _exporter: TestExporter
    _semaphore: asyncio.Semaphore

    def __init__(self, spec_manager: TestSpecManager, exporter: TestExporter) -> None:
        self._spec_manager = spec_manager
        self._exporter = exporter
        self._semaphore = asyncio.Semaphore(_DEFAULT_CONCURRENCY)

    async def _run_spec(self, spec: TestSpec) -> None:
        """
        Run a single test specification.
        """
        async with self._semaphore:
            runner = TestRunner(spec, self._exporter)
            await runner.run()

    async def run_all(self) -> None:
        """
        Run all test specifications.
        """
        tasks = []
        for spec in self._spec_manager.all_specs():
            tasks.append(asyncio.create_task(self._run_spec(spec)))
        await asyncio.gather(*tasks)

    async def run_by_tag(self, tag: TestTag) -> None:
        """
        Run test specifications by tag.
        """
        tasks = []
        for spec in self._spec_manager.specs_by_tag(tag):
            tasks.append(asyncio.create_task(self._run_spec(spec)))
        await asyncio.gather(*tasks)

    async def run_by_name(self, name: str) -> None:
        """
        Run test specification by name.
        """
        spec = self._spec_manager.spec_by_name(name)
        await self._run_spec(spec)
