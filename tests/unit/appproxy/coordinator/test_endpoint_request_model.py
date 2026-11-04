from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import UUID

import pytest

from ai.backend.appproxy.coordinator.api.endpoint import (
    EndpointCreationRequestModel,
    _request_model_to_item,
)
from ai.backend.common.data.entity.deployment import DeploymentID
from ai.backend.common.data.entity.domain import DomainName
from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.dto.appproxy_coordinator.v2.endpoint.types import (
    EndpointTagsModel,
    SessionTagsModel,
    TagsModel,
)
from ai.backend.common.exception import BackendAISchemaValidationFailed

_DEPLOYMENT_ID = DeploymentID(UUID("aaaaaaaa-0000-4000-8000-000000000001"))
_USER_ID = UserID(UUID("bbbbbbbb-0000-4000-8000-000000000001"))
_PROJECT_ID = ProjectID(UUID("cccccccc-0000-4000-8000-000000000001"))
_DOMAIN_NAME = DomainName("default")


@dataclass(frozen=True)
class _MalformedTagIdCase:
    tag_section: str
    field_name: str


class TestEndpointCreationRequestModel:
    @pytest.fixture
    def single_endpoint_request_body(self) -> dict[str, Any]:
        return {
            "version": "v2",
            "service_name": "echo",
            "tags": {
                "session": {
                    "user_uuid": str(_USER_ID),
                    "project_id": str(_PROJECT_ID),
                    "domain_name": str(_DOMAIN_NAME),
                },
                "endpoint": {
                    "id": str(_DEPLOYMENT_ID),
                    "runtime_variant": "custom",
                    "existing_url": None,
                },
            },
        }

    @pytest.fixture
    def request_body_with_malformed_tag_id(
        self, case: _MalformedTagIdCase, single_endpoint_request_body: dict[str, Any]
    ) -> dict[str, Any]:
        single_endpoint_request_body["tags"][case.tag_section][case.field_name] = "not-a-uuid"
        return single_endpoint_request_body

    def test_item_carries_the_request_tags_as_typed_ids(
        self, single_endpoint_request_body: dict[str, Any]
    ) -> None:
        request = EndpointCreationRequestModel.model_validate(single_endpoint_request_body)
        item = _request_model_to_item(_DEPLOYMENT_ID, request)
        assert item.tags == TagsModel(
            session=SessionTagsModel(
                user_uuid=_USER_ID, project_id=_PROJECT_ID, domain_name=_DOMAIN_NAME
            ),
            endpoint=EndpointTagsModel(
                id=_DEPLOYMENT_ID, runtime_variant="custom", existing_url=None
            ),
        )

    def test_tags_dump_to_the_json_they_were_read_from(
        self, single_endpoint_request_body: dict[str, Any]
    ) -> None:
        request = EndpointCreationRequestModel.model_validate(single_endpoint_request_body)
        assert request.tags.model_dump(mode="json") == single_endpoint_request_body["tags"]

    @pytest.mark.parametrize(
        "case",
        [
            _MalformedTagIdCase(tag_section="session", field_name="user_uuid"),
            _MalformedTagIdCase(tag_section="session", field_name="project_id"),
            _MalformedTagIdCase(tag_section="endpoint", field_name="id"),
        ],
        ids=lambda case: f"{case.tag_section}-{case.field_name}",
    )
    def test_rejects_a_tag_id_that_is_not_a_uuid(
        self, request_body_with_malformed_tag_id: dict[str, Any]
    ) -> None:
        with pytest.raises(BackendAISchemaValidationFailed):
            EndpointCreationRequestModel.model_validate(request_body_with_malformed_tag_id)
