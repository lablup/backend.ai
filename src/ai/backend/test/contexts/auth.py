from ai.backend.test.testcases.context import BaseTestContext
from ai.backend.test.tester.config import Endpoint, KeyPair, LoginCredential


class KeypairContext(BaseTestContext[KeyPair]):
    @classmethod
    def name(cls) -> str:
        return "keypair"


class EndpointContext(BaseTestContext[Endpoint]):
    @classmethod
    def name(cls) -> str:
        return "endpoint"


class LoginCredentialContext(BaseTestContext[LoginCredential]):
    @classmethod
    def name(cls) -> str:
        return "login_credential"
