from ai.backend.client.session import AsyncSession
from ai.backend.test.contexts.context import BaseTestContext, ContextName


class ClientSessionContext(BaseTestContext[AsyncSession]):
    @classmethod
    def name(cls) -> ContextName:
        return ContextName.CLIENT_SESSION


class CreatedUserClientSessionContext(BaseTestContext[AsyncSession]):
    @classmethod
    def name(cls) -> ContextName:
        return ContextName.CREATED_USER_CLIENT_SESSION
