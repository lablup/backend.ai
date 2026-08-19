from typing import override

from ai.backend.test.contexts.context import BaseTestContext, ContextName
from ai.backend.test.tester.dependency import (
    EndpointDep,
    KeyPairDep,
    LoginCredentialDep,
)


class KeypairContext(BaseTestContext[KeyPairDep]):
    @classmethod
    @override
    def name(cls) -> ContextName:
        return ContextName.KEYPAIR


class LoginCredentialContext(BaseTestContext[LoginCredentialDep]):
    @classmethod
    @override
    def name(cls) -> ContextName:
        return ContextName.LOGIN_CREDENTIAL


class EndpointContext(BaseTestContext[EndpointDep]):
    @classmethod
    @override
    def name(cls) -> ContextName:
        return ContextName.ENDPOINT
