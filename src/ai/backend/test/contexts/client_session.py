from ai.backend.client.session import AsyncSession
from ai.backend.test.testcases.context import BaseTestContext


class ClientSessionContext(BaseTestContext[AsyncSession]):
    @classmethod
    def name(cls) -> str:
        return "client_session"
