from ai.backend.client.session import AsyncSession, Session
from ai.backend.test.contexts.context import BaseTestContext, ContextName


class ClientSessionContext(BaseTestContext[AsyncSession]):
    @classmethod
    def name(cls) -> ContextName:
        return ContextName.CLIENT_SESSION


class ClientSyncSessionContext(BaseTestContext[Session]):
    @classmethod
    def name(cls) -> ContextName:
        return ContextName.CLIENT_SESSION
