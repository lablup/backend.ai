from ai.backend.test.contexts.context import BaseTestContext, ContextName
from ai.backend.test.tester.config import (
    EndpointConfig,
    KeyPairConfig,
    LoginCredentialConfig,
)


class KeypairContext(BaseTestContext[KeyPairConfig]):
    @classmethod
    def name(cls) -> ContextName:
        return ContextName.KEYPAIR


class LoginCredentialContext(BaseTestContext[LoginCredentialConfig]):
    @classmethod
    def name(cls) -> ContextName:
        return ContextName.LOGIN_CREDENTIAL


class EndpointContext(BaseTestContext[EndpointConfig]):
    @classmethod
    def name(cls) -> ContextName:
        return ContextName.ENDPOINT
