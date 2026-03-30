from ai.backend.test.contexts.context import BaseTestContext, ContextName
from ai.backend.test.tester.dependency import (
    EndpointDep,
    KeyPairDep,
    LoginCredentialDep,
)


class KeypairContext(BaseTestContext[KeyPairDep]):
    @classmethod
    def name(cls) -> ContextName:
        return ContextName.KEYPAIR


class LoginCredentialContext(BaseTestContext[LoginCredentialDep]):
    @classmethod
    def name(cls) -> ContextName:
        return ContextName.LOGIN_CREDENTIAL


class EndpointContext(BaseTestContext[EndpointDep]):
    @classmethod
    def name(cls) -> ContextName:
        return ContextName.ENDPOINT
