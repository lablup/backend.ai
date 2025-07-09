from typing import override

from ai.backend.client.exceptions import BackendAPIError
from ai.backend.test.contexts.client_session import ClientSessionContext
from ai.backend.test.contexts.model_service import (
    CreatedModelServiceEndpointMetaContext,
)
from ai.backend.test.contexts.resource_policy import UserResourcePolicyContext
from ai.backend.test.templates.template import TestCode
from ai.backend.test.utils.exceptions import UnexpectedSuccess


class ReplicasScaleFailureTooManySessions(TestCode):
    """
    Test case to verify that scaling replicas beyond the maximum allowed sessions fails
    """

    @override
    async def test(self) -> None:
        client_session = ClientSessionContext.current()
        model_service_endpoint_meta = CreatedModelServiceEndpointMetaContext.current()
        service_id = model_service_endpoint_meta.service_id

        user_resource_policy_dep = UserResourcePolicyContext.current()
        resource_policy_info = await client_session.UserResourcePolicy(
            name=user_resource_policy_dep.name
        ).get_info()
        max_session_count_per_model_service = resource_policy_info[
            "max_session_count_per_model_session"
        ]

        try:
            await client_session.Service(id=service_id).scale(
                max_session_count_per_model_service + 1
            )
            raise UnexpectedSuccess(
                "Expected BackendAPIError for overscaling replicas was not raised"
            )
        except BackendAPIError as e:
            assert e.status == 400
            assert e.data["error_code"] == "api_parsing_invalid-parameters"
