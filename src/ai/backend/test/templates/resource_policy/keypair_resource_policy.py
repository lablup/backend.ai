from contextlib import asynccontextmanager as actxmgr
from typing import AsyncIterator, override

from ai.backend.client.output.fields import keypair_fields
from ai.backend.test.contexts.auth import KeypairContext
from ai.backend.test.contexts.client_session import ClientSessionContext
from ai.backend.test.contexts.resource_policy import KeypairResourcePolicyContext
from ai.backend.test.templates.template import (
    WrapperTestTemplate,
)


class KeypairResourcePolicyTemplate(WrapperTestTemplate):
    @property
    def name(self) -> str:
        return "keypair_resource_policy"

    @override
    @actxmgr
    async def _context(self) -> AsyncIterator[None]:
        keypair_dep = KeypairContext.current()
        client_session = ClientSessionContext.current()
        keypair_resource_policy = KeypairResourcePolicyContext.current()

        access_key = keypair_dep.access_key
        result = await client_session.KeyPair(access_key).info([keypair_fields["resource_policy"]])
        keypair_resource_policy_name = result["resource_policy"]

        await client_session.KeypairResourcePolicy.update(
            keypair_resource_policy_name,
            max_concurrent_sessions=keypair_resource_policy.max_concurrent_sessions,
            max_containers_per_session=keypair_resource_policy.max_containers_per_session,
            max_session_lifetime=keypair_resource_policy.max_session_lifetime,
        )
        yield
        # TODO: Should we restore with the original resource policy?
