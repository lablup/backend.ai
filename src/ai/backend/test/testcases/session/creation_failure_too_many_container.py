from ai.backend.client.exceptions import BackendAPIError
from ai.backend.client.output.fields import keypair_fields, keypair_resource_policy_fields
from ai.backend.common.types import ClusterMode
from ai.backend.test.contexts.client_session import ClientSessionContext
from ai.backend.test.contexts.config import (
    ImageConfigContext,
    KeypairConfigContext,
    SessionConfigContext,
)
from ai.backend.test.templates.template import TestCode


class SessionCreationFailureTooManyContainer(TestCode):
    async def test(self) -> None:
        keypair = KeypairConfigContext.current()
        client_session = ClientSessionContext.current()
        image = ImageConfigContext.current()
        session_config = SessionConfigContext.current()
        session_name = "test-session-creation-failure"

        access_key = keypair.access_key
        result = await client_session.KeyPair(access_key).info([keypair_fields["resource_policy"]])
        keypair_resource_policy_name = result["resource_policy"]

        result = await client_session.KeypairResourcePolicy(access_key).info(
            keypair_resource_policy_name,
            [keypair_resource_policy_fields["max_containers_per_session"]],
        )
        max_containers_per_session = result["max_containers_per_session"]

        try:
            await client_session.ComputeSession.get_or_create(
                image.name,
                architecture=image.architecture,
                name=session_name,
                resources=session_config.resources,
                cluster_mode=ClusterMode.SINGLE_NODE,
                cluster_size=max_containers_per_session + 1,  # Exceeding the limit
            )
        except BackendAPIError as e:
            assert e.data["error_code"] == "session_create_unavailable"
