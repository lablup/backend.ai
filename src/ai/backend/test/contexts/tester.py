from pathlib import Path
from typing import override

from ai.backend.test.contexts.context import BaseTestContext, ContextName
from ai.backend.test.data.tester import TestSpecMeta


class TestSpecMetaContext(BaseTestContext[TestSpecMeta]):
    @classmethod
    @override
    def name(cls) -> ContextName:
        return ContextName.TEST_SPEC_META


class TestErrorOutputDirectoryContext(BaseTestContext[Path]):
    @classmethod
    @override
    def name(cls) -> ContextName:
        return ContextName.TEST_ERROR_OUTPUT_DIRECTORY
