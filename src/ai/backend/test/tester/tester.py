import asyncio
from contextlib import ExitStack
from pathlib import Path
from typing import Any, Mapping, Optional, Type, cast

import aiofiles
import aiotools
import tomli

from ai.backend.test.contexts.context import BaseTestContext, ContextName
from ai.backend.test.tester.config import TesterConfig

from ..testcases.spec_manager import TestSpec, TestSpecManager, TestTag
from .exporter import TestExporter
from .runner import TestRunner


class Tester:
    _spec_manager: TestSpecManager
    _exporter_type: Type[TestExporter]
    _config_file_path: Path
    _config: Optional[TesterConfig]
    _semaphore_instance: Optional[asyncio.Semaphore]

    def __init__(
        self,
        spec_manager: TestSpecManager,
        exporter_type: Type[TestExporter],
        config_file_path: Path,
    ) -> None:
        self._spec_manager = spec_manager
        self._exporter_type = exporter_type
        self._config_file_path = config_file_path
        self._config = None
        self._semaphore_instance = None

    @property
    def _semaphore(self) -> asyncio.Semaphore:
        if not self._config:
            raise RuntimeError("Tester configuration is not loaded")

        if self._semaphore_instance is None:
            self._semaphore_instance = asyncio.Semaphore(self._config.runner.concurrency)
        return self._semaphore_instance

    @aiotools.lru_cache(maxsize=1)
    async def _load_tester_config(self, config_path: Path) -> TesterConfig:
        async with aiofiles.open(config_path, mode="r") as fp:
            raw_content = await fp.read()
            content = tomli.loads(raw_content)
            config = TesterConfig.model_validate(content, by_alias=True, by_name=True)
            return config

    async def _run_single_spec(self, spec: TestSpec, sub_name: Optional[str] = None) -> None:
        async with self._semaphore:
            exporter = await self._exporter_type.create(sub_name)
            runner = TestRunner(spec, exporter)
            await runner.run()

    async def _run_param_spec(self, spec: TestSpec, param: Mapping[ContextName, Any]) -> None:
        registered_contexts = BaseTestContext.used_contexts()
        with ExitStack() as local_stack:
            for ctx_name, value in param.items():
                if ctx := registered_contexts.get(ctx_name):
                    # Create a context manager for the parameterized context
                    ctx_mgr = ctx.with_current(value)
                    local_stack.enter_context(ctx_mgr)
            await self._run_single_spec(spec, self._param_to_name(param))

    def _param_to_name(self, param: Mapping[ContextName, Any]) -> Optional[str]:
        if not param:
            return None
        param_str = "_".join(f"{key}={value}" for key, value in sorted(param.items()))
        return f"({param_str})"

    async def _run_spec(self, spec: TestSpec) -> None:
        """
        Run a single test specification.
        """
        if not self._config:
            raise RuntimeError("Tester configuration is not loaded")

        registered_contexts = BaseTestContext.used_contexts()
        with ExitStack() as global_stack:
            # global context manager for the tester
            for key, ctx in registered_contexts.items():
                if config := getattr(self._config.context, key, None):
                    ctx_mgr = ctx.with_current(config)
                    global_stack.enter_context(ctx_mgr)
            parametrizes = spec.product_parametrizes()
            if parametrizes:
                for param in parametrizes:
                    await self._run_param_spec(spec, param)
                return
            await self._run_single_spec(spec)

    async def run(self) -> None:
        """
        Run all test specifications.
        """
        self._config = await self._load_tester_config(self._config_file_path)
        exclude_tags = cast(TesterConfig, self._config).runner.exclude_tags

        tasks = []
        for spec in self._spec_manager.all_specs():
            if spec.tags & exclude_tags:
                continue
            tasks.append(asyncio.create_task(self._run_spec(spec)))
        await asyncio.gather(*tasks)

    async def run_all(self) -> None:
        """
        Run all test specifications.
        """
        self._config = await self._load_tester_config(self._config_file_path)
        tasks = []
        for spec in self._spec_manager.all_specs():
            tasks.append(asyncio.create_task(self._run_spec(spec)))
        await asyncio.gather(*tasks)

    async def run_by_tag(self, tag: TestTag) -> None:
        """
        Run test specifications by tag.
        """
        self._config = await self._load_tester_config(self._config_file_path)
        tasks = []
        for spec in self._spec_manager.specs_by_tag(tag):
            tasks.append(asyncio.create_task(self._run_spec(spec)))
        await asyncio.gather(*tasks)

    async def run_by_name(self, name: str) -> None:
        """
        Run test specification by name.
        """
        self._config = await self._load_tester_config(self._config_file_path)
        spec = self._spec_manager.spec_by_name(name)
        await self._run_spec(spec)
