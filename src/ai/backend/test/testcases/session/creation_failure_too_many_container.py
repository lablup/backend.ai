from ai.backend.client.exceptions import BackendAPIError
from ai.backend.client.output.fields import keypair_fields, keypair_resource_policy_fields
from ai.backend.common.types import ClusterMode
from ai.backend.test.contexts.auth import KeypairContext
from ai.backend.test.contexts.client_session import ClientSessionContext
from ai.backend.test.contexts.image import ImageContext
from ai.backend.test.contexts.session import SessionContext
from ai.backend.test.contexts.tester import TestSpecMetaContext
from ai.backend.test.templates.template import TestCode
from ai.backend.test.utils.exceptions import UnexpectedSuccess


class SessionCreationFailureTooManyContainer(TestCode):
    async def test(self) -> None:
        keypair = KeypairContext.current()
        client_session = ClientSessionContext.current()
        image_dep = ImageContext.current()
        session_dep = SessionContext.current()
        spec_meta = TestSpecMetaContext.current()
        test_id = spec_meta.test_id
        session_name = f"test_failure_{str(test_id)}"

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
                image_dep.name,
                architecture=image_dep.architecture,
                name=session_name,
                resources=session_dep.resources,
                cluster_mode=ClusterMode.SINGLE_NODE,
                cluster_size=max_containers_per_session + 1,  # Exceeding the limit
            )
            raise UnexpectedSuccess(
                "Expected BackendAPIError for exceeding max containers limit was not raised"
            )
        except BackendAPIError as e:
            assert e.data["error_code"] == "session_create_unavailable"
