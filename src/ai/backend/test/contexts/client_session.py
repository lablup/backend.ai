from ai.backend.client.session import BaseSession
from ai.backend.test.contexts.context import BaseTestContext, ContextName


class ClientSessionContext(BaseTestContext[BaseSession]):
    @classmethod
    def name(cls) -> ContextName:
        return ContextName.CLIENT_SESSION
