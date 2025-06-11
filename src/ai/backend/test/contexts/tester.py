import uuid

from ai.backend.test.testcases.context import BaseTestContext


class TestIDContext(BaseTestContext[uuid.UUID]):
    @classmethod
    def get_name(cls) -> str:
        return "test_id"
