import asyncio
from pathlib import Path
from typing import Optional

import aiofiles
from ai.backend.test.testcases.context import BaseTestContext
import aiotools
import tomli

from ai.backend.test.contexts.api_config import APIConfigContext
from ai.backend.test.contexts.tester_config import TestConfigContext
from ai.backend.test.tester.types import TesterConfigModel

from ..testcases.testcases import TestSpec, TestSpecManager, TestTag
from .exporter import TestExporter
from .runner import TestRunner

_DEFAULT_CONCURRENCY = 10


class Tester:
    _spec_manager: TestSpecManager
    _exporter: TestExporter
    _test_users: list[str]
    _semaphore: asyncio.Semaphore

    def __init__(
        self, spec_manager: TestSpecManager, exporter: TestExporter, test_users: list[str]
    ) -> None:
        self._spec_manager = spec_manager
        self._exporter = exporter
        self._test_users = test_users
        self._semaphore = asyncio.Semaphore(_DEFAULT_CONCURRENCY)
    
    @aiotools.lru_cache(maxsize=1)
    async def load_tester_config(self, config_path: Path) -> TesterConfigModel:
        async with aiofiles.open(config_path, mode="r") as fp:
            raw_content = await fp.read()
            content = tomli.loads(raw_content)
            config = TesterConfigModel.model_validate(content, by_alias=True)
            return config
    
    async def _run_spec(self, spec: TestSpec) -> None:
        """
        Run a single test specification.
        """
        tester_config = await self.load_tester_config()
        ctx_map = BaseTestContext.get_used_contexts()
        ctx_map["endpoint"].with_current(config.contexts.endpoint)
        ctx_map["key_pair"].with_current(config.contexts.key_pair)
        ctx_map["login_cred"].with_current(config.contexts.login_cred)
        with TestConfigContext.with_current(tester_config):
            for test_user in self._test_users:
                config = tester_config.api_configs[test_user].to_api_config()
                with APIConfigContext.with_current(config):
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
