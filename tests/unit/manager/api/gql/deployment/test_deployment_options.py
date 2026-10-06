from __future__ import annotations

from typing import cast

import pytest
import strawberry
from strawberry.experimental.pydantic.conversion_types import StrawberryTypeFromPydantic

from ai.backend.common.api_handlers import BaseResponseModel
from ai.backend.common.dto.manager.v2.deployment_options.response import DeploymentOptionsInfo
from ai.backend.common.dto.manager.v2.session_options.response import SessionHandlerOptionsInfo
from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.manager.api.gql.decorators import BackendAIGQLMeta, gql_pydantic_type
from ai.backend.manager.api.gql.deployment.types.deployment_options import DeploymentOptionsInfoGQL
from ai.backend.manager.api.gql.session_options.types import (
    DefaultSessionHandlerOptionsPolicyInfoGQL,
)


class OptionsResponse(BaseResponseModel):
    deployment: DeploymentOptionsInfo
    session: SessionHandlerOptionsInfo


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version=NEXT_RELEASE_VERSION,
        description="Deployment and session options test query.",
    ),
    model=OptionsResponse,
    name="OptionsQuery",
)
class OptionsQueryGQL:
    deployment: DeploymentOptionsInfoGQL
    session: DefaultSessionHandlerOptionsPolicyInfoGQL


class TestDeploymentOptionsInfoGQL:
    @pytest.fixture(params=["default", "by_handler", "null_values"])
    def options(self, request: pytest.FixtureRequest) -> OptionsResponse:
        policy: dict[str, object] = {
            "default": {"timeout_sec": None, "max_retry_count": 5},
            "by_handler": [],
        }
        if request.param == "by_handler":
            policy["by_handler"] = [
                {"handler_name": "test", "timeout_sec": 30, "max_retry_count": 3}
            ]
        elif request.param == "null_values":
            policy["default"] = {"timeout_sec": None, "max_retry_count": None}
            policy["by_handler"] = [
                {"handler_name": "test", "timeout_sec": None, "max_retry_count": None}
            ]
        return OptionsResponse.model_validate({
            "deployment": {"handler_options": policy},
            "session": policy,
        })

    async def test_deployment_and_session_handler_options(self, options: OptionsResponse) -> None:
        schema = strawberry.Schema(query=OptionsQueryGQL)
        query_type = cast(type[StrawberryTypeFromPydantic[OptionsResponse]], OptionsQueryGQL)
        result = await schema.execute(
            """{
                deployment {
                    handlerOptions {
                        default { __typename timeoutSec maxRetryCount }
                        byHandler { __typename handlerName timeoutSec maxRetryCount }
                    }
                }
                session {
                    default { __typename timeoutSec maxRetryCount }
                    byHandler { __typename handlerName timeoutSec maxRetryCount }
                }
            }""",
            root_value=query_type.from_pydantic(options),
        )

        assert result.errors is None
        assert result.data is not None
        for key, typename in (
            ("deployment", "HandlerOptions"),
            ("session", "DefaultSessionHandlerOptions"),
        ):
            policy = result.data[key]
            if key == "deployment":
                policy = policy["handlerOptions"]
            assert policy["default"] == {
                "__typename": f"{typename}Info",
                "timeoutSec": options.session.default.timeout_sec,
                "maxRetryCount": options.session.default.max_retry_count,
            }
            assert policy["byHandler"] == [
                {
                    "__typename": f"{typename}EntryInfo",
                    "handlerName": entry.handler_name,
                    "timeoutSec": entry.timeout_sec,
                    "maxRetryCount": entry.max_retry_count,
                }
                for entry in options.session.by_handler
            ]
