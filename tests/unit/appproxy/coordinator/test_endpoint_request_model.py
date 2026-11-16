from __future__ import annotations

from uuid import UUID

import pytest

from ai.backend.appproxy.coordinator.api.endpoint import (
    EndpointCreationRequestModel,
    _request_model_to_item,
)
from ai.backend.common.data.entity.deployment import DeploymentID
from ai.backend.common.dto.appproxy_coordinator.v2.endpoint.types import (
    EndpointTagsModel,
    SessionTagsModel,
    TagsModel,
)

_DEPLOYMENT_ID = DeploymentID(UUID("aaaaaaaa-0000-4000-8000-000000000001"))
_USER_ID = "bbbbbbbb-0000-4000-8000-000000000001"
_PROJECT_ID = "cccccccc-0000-4000-8000-000000000001"


class TestRequestModelToItem:
    @pytest.fixture
    def single_endpoint_request(self) -> EndpointCreationRequestModel:
        return EndpointCreationRequestModel.model_validate({
            "version": "v2",
            "service_name": "echo",
            "tags": {
                "session": {
                    "user_uuid": _USER_ID,
                    "project_id": _PROJECT_ID,
                    "domain_name": "default",
                },
                "endpoint": {
                    "id": str(_DEPLOYMENT_ID),
                    "runtime_variant": "custom",
                    "existing_url": None,
                },
            },
        })

    def test_carries_the_uuid_tags_of_the_request_as_strings(
        self, single_endpoint_request: EndpointCreationRequestModel
    ) -> None:
        item = _request_model_to_item(_DEPLOYMENT_ID, single_endpoint_request)
        assert item.tags == TagsModel(
            session=SessionTagsModel(
                user_uuid=_USER_ID, project_id=_PROJECT_ID, domain_name="default"
            ),
            endpoint=EndpointTagsModel(
                id=str(_DEPLOYMENT_ID), runtime_variant="custom", existing_url=None
            ),
        )
