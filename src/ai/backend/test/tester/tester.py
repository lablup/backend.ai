import asyncio
from contextlib import ExitStack
from pathlib import Path

import aiofiles
import aiotools
import tomli

from ai.backend.test.testcases.context import BaseTestContext
from ai.backend.test.tester.config import TesterConfig

from ..testcases.testcases import TestSpec, TestSpecManager, TestTag
from .exporter import TestExporter
from .runner import TestRunner

_DEFAULT_CONCURRENCY = 10


class Tester:
    _spec_manager: TestSpecManager
    _exporter: TestExporter
    _semaphore: asyncio.Semaphore
    _config_file_path: Path

    def __init__(
        self, spec_manager: TestSpecManager, exporter: TestExporter, config_file_path: Path
    ) -> None:
        self._spec_manager = spec_manager
        self._exporter = exporter
        self._config_file_path = config_file_path
        self._semaphore = asyncio.Semaphore(_DEFAULT_CONCURRENCY)

    @aiotools.lru_cache(maxsize=1)
    async def _load_tester_config(self, config_path: Path) -> TesterConfig:
        async with aiofiles.open(config_path, mode="r") as fp:
            raw_content = await fp.read()
            content = tomli.loads(raw_content)
            config = TesterConfig.model_validate(content, by_alias=True)
            return config

    async def _run_spec(self, spec: TestSpec) -> None:
        """
        Run a single test specification.
        """
        tester_config = await self._load_tester_config(self._config_file_path)
        ctx_map = BaseTestContext.get_used_contexts()

        async with self._semaphore:
            with ExitStack() as stack:
                for key, ctx in ctx_map.items():
                    if config := getattr(tester_config.context, key, None):
                        ctx_mgr = ctx.with_current(config)
                        stack.enter_context(ctx_mgr)

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
