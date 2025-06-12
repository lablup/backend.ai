from ai.backend.client.exceptions import BackendAPIError
from ai.backend.client.output.fields import keypair_fields, keypair_resource_policy_fields
from ai.backend.client.session import AsyncSession
from ai.backend.common.types import ClusterMode
from ai.backend.test.templates.template import TestCode

# Test environment configuration
# TODO: Make these configurable loaderable by template wrapper
_IMAGE_NAME = "cr.backend.ai/stable/python:3.9-ubuntu20.04"


class SessionCreationFailureTooManyContainer(TestCode):
    def __init__(self) -> None:
        super().__init__()

    async def test(self) -> None:
        async with AsyncSession() as client_session:
            session_name = "test-session-creation-failure"

            # TODO: Replace this KeypairContext
            access_key = "AKIAHUKCHDEZGEXAMPLE"
            result = await client_session.KeyPair(access_key).info([
                keypair_fields["resource_policy"]
            ])
            keypair_resource_policy_name = result["resource_policy"]

            result = await client_session.KeypairResourcePolicy(access_key).info(
                keypair_resource_policy_name,
                [keypair_resource_policy_fields["max_containers_per_session"]],
            )
            max_containers_per_session = result["max_containers_per_session"]

            try:
                await client_session.ComputeSession.get_or_create(
                    _IMAGE_NAME,
                    name=session_name,
                    resources={"cpu": 1, "mem": "512m"},
                    cluster_mode=ClusterMode.SINGLE_NODE,
                    cluster_size=max_containers_per_session + 1,  # Exceeding the limit
                )
            except BackendAPIError as e:
                assert e.data["error_code"] == "session_create_unavailable"
