from typing import NewType

from callosum.auth import (
    AbstractClientAuthenticator,
    AbstractServerAuthenticator,
    AuthResult,
    Credential,
    Identity,
)

PublicKey = NewType("PublicKey", bytes)
SecretKey = NewType("SecretKey", bytes)


class ManagerAuthHandler(AbstractClientAuthenticator):
    def __init__(
        self,
        domain: str,
        agent_public_key: PublicKey,
        manager_public_key: PublicKey,
        manager_secret_key: SecretKey,
    ) -> None:
        self.domain = domain
        self._agent_public_key = agent_public_key
        self._manager_public_key = manager_public_key
        self._manager_secret_key = manager_secret_key

    async def server_public_key(self) -> bytes:
        return self._agent_public_key

    async def client_public_key(self) -> bytes:
        return self._manager_public_key

    async def client_identity(self) -> Identity:
        assert self._manager_secret_key is not None
        return Identity(self.domain, self._manager_secret_key)


class AgentAuthHandler(AbstractServerAuthenticator):
    def __init__(
        self,
        domain: str,
        manager_public_key: PublicKey,
        agent_public_key: PublicKey,
        agent_secret_key: SecretKey,
    ) -> None:
        self.domain = domain
        self._manager_public_key = manager_public_key
        self._agent_public_key = agent_public_key
        self._agent_secret_key = agent_secret_key

    async def server_public_key(self) -> bytes:
        return self._agent_public_key

    async def server_identity(self) -> Identity:
        assert self._agent_secret_key is not None
        return Identity(self.domain, self._agent_secret_key)

    async def check_client(self, creds: Credential) -> AuthResult:
        if creds.domain == self.domain and creds.public_key == self._manager_public_key:
            return AuthResult(success=True, user_id="manager")
        return AuthResult(success=False)
