from callosum.auth import (
    AbstractClientAuthenticator,
    AbstractServerAuthenticator,
    AuthResult,
    Credential,
    Identity,
)
from zmq.auth.certs import load_certificate


class ManagerAuthHandler(AbstractClientAuthenticator):
    def __init__(self, domain: str) -> None:
        self.domain = domain
        # TODO: load manager identity from a local certificate
        # TODO: expose the manager certificate in the admin UI
        self.manager_pub_id, self.manager_id = load_certificate(
            "fixtures/manager/manager.key_secret"
        )

    async def server_public_key(self) -> bytes:
        # TODO: load per-agent public key from database
        #       (need to extend the "agents" table)
        # NOTE: we need to use contextvars to localize the target agent
        #       without altering the authenticator interface.
        # TODO: implement the per-agent certificate mgmt UI
        pub, _ = load_certificate("fixtures/agent/agent.key")
        return pub

    async def client_public_key(self) -> bytes:
        return self.manager_pub_id

    async def client_identity(self) -> Identity:
        assert self.manager_id is not None
        return Identity(self.domain, self.manager_id)


class AgentAuthHandler(AbstractServerAuthenticator):
    def __init__(self, domain: str) -> None:
        self.domain = domain
        # TODO: load known manager public key from local_config
        self.manager_pub_id, _ = load_certificate("fixtures/manager/manager.key")
        # TODO: load agent identity from a local certificate
        self.agent_pub_id, self.agent_id = load_certificate("fixtures/agent/agent.key_secret")

    async def server_public_key(self) -> bytes:
        return self.agent_pub_id

    async def server_identity(self) -> Identity:
        assert self.agent_id is not None
        return Identity(self.domain, self.agent_id)

    async def check_client(self, creds: Credential) -> AuthResult:
        if creds.domain == self.domain and creds.public_key == self.manager_pub_id:
            return AuthResult(success=True, user_id="manager")
        return AuthResult(success=False)
