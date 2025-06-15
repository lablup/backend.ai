from ai.backend.test.contexts.context import BaseTestContext, ContextName
from ai.backend.test.tester.config import (
    EndpointConfig,
    KeyPairConfig,
    LoginCredentialConfig,
)


class KeypairConfigContext(BaseTestContext[KeyPairConfig]):
    @classmethod
    def name(cls) -> ContextName:
        return ContextName.KEYPAIR


class LoginCredentialConfigContext(BaseTestContext[LoginCredentialConfig]):
    @classmethod
    def name(cls) -> ContextName:
        return ContextName.LOGIN_CREDENTIAL


class EndpointConfigContext(BaseTestContext[EndpointConfig]):
    @classmethod
    def name(cls) -> ContextName:
        return ContextName.ENDPOINT
