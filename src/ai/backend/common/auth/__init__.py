from callosum.auth import (
    AbstractClientAuthenticator,
    AbstractServerAuthenticator,
    AuthResult,
    Credential,
    Identity,
)


class ManagerAuthHandler(AbstractClientAuthenticator):
    def __init__(
        self,
        domain: str,
        agent_pub_id: bytes,
        manager_pub_id: bytes,
        manager_id: bytes,
    ) -> None:
        self.domain = domain
        self.agent_pub_id = agent_pub_id
        self.manager_pub_id = manager_pub_id
        self.manager_id = manager_id

    async def server_public_key(self) -> bytes:
        return self.agent_pub_id

    async def client_public_key(self) -> bytes:
        return self.manager_pub_id

    async def client_identity(self) -> Identity:
        assert self.manager_id is not None
        return Identity(self.domain, self.manager_id)


class AgentAuthHandler(AbstractServerAuthenticator):
    def __init__(
        self,
        domain: str,
        manager_pub_id: bytes,
        agent_pub_id: bytes,
        agent_id: bytes,
    ) -> None:
        self.domain = domain
        self.manager_pub_id = manager_pub_id
        self.agent_pub_id = agent_pub_id
        self.agent_id = agent_id

    async def server_public_key(self) -> bytes:
        return self.agent_pub_id

    async def server_identity(self) -> Identity:
        assert self.agent_id is not None
        return Identity(self.domain, self.agent_id)

    async def check_client(self, creds: Credential) -> AuthResult:
        if creds.domain == self.domain and creds.public_key == self.manager_pub_id:
            return AuthResult(success=True, user_id="manager")
        return AuthResult(success=False)
