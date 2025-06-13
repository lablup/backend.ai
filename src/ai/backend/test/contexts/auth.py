from ai.backend.test.contexts.context import BaseTestContext, ContextName
from ai.backend.test.tester.config import Endpoint, KeyPair, LoginCredential


class KeypairContext(BaseTestContext[KeyPair]):
    @classmethod
    def name(cls) -> ContextName:
        return ContextName.KEYPAIR


class EndpointContext(BaseTestContext[Endpoint]):
    @classmethod
    def name(cls) -> ContextName:
        return ContextName.ENDPOINT


class LoginCredentialContext(BaseTestContext[LoginCredential]):
    @classmethod
    def name(cls) -> ContextName:
        return ContextName.LOGIN_CREDENTIAL
