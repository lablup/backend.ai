from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import pytest
from pydantic import ValidationError

from ai.backend.common.dto.manager.template.request import (
    CreateClusterTemplateRequest,
    CreateSessionTemplateRequest,
    DeleteClusterTemplateRequest,
    DeleteSessionTemplateRequest,
    GetClusterTemplateRequest,
    GetSessionTemplateRequest,
    ListClusterTemplatesRequest,
    ListSessionTemplatesRequest,
    TemplatePathParam,
    UpdateClusterTemplateRequest,
    UpdateSessionTemplateRequest,
)
from ai.backend.common.dto.manager.template.response import (
    ClusterTemplateListItemDTO,
    CreateClusterTemplateResponse,
    CreateSessionTemplateResponse,
    DeleteClusterTemplateResponse,
    DeleteSessionTemplateResponse,
    GetClusterTemplateResponse,
    GetSessionTemplateResponse,
    ListClusterTemplatesResponse,
    ListSessionTemplatesResponse,
    SessionTemplateItemDTO,
    SessionTemplateListItemDTO,
    UpdateClusterTemplateResponse,
    UpdateSessionTemplateResponse,
)

_NOW = datetime.now(UTC)


class TestTemplatePathParam:
    def test_basic_instantiation(self) -> None:
        param = TemplatePathParam(template_id="abc123")
        assert param.template_id == "abc123"


class TestCreateSessionTemplateRequest:
    def test_with_defaults(self) -> None:
        req = CreateSessionTemplateRequest(payload='{"template": {}}')
        assert req.group == "default"
        assert req.domain == "default"
        assert req.owner_access_key is None
        assert req.payload == '{"template": {}}'

    def test_with_all_fields(self) -> None:
        req = CreateSessionTemplateRequest(
            group="mygroup",
            domain="mydomain",
            owner_access_key="AKSOMEKEY",
            payload='{"template": {}}',
        )
        assert req.group == "mygroup"
        assert req.domain == "mydomain"
        assert req.owner_access_key == "AKSOMEKEY"

    @pytest.mark.parametrize("alias", ["group", "groupName", "group_name"])
    def test_group_alias(self, alias: str) -> None:
        req = CreateSessionTemplateRequest.model_validate({
            alias: "testgroup",
            "payload": "{}",
        })
        assert req.group == "testgroup"

    @pytest.mark.parametrize("alias", ["domain", "domainName", "domain_name"])
    def test_domain_alias(self, alias: str) -> None:
        req = CreateSessionTemplateRequest.model_validate({
            alias: "testdomain",
            "payload": "{}",
        })
        assert req.domain == "testdomain"


class TestListSessionTemplatesRequest:
    def test_defaults(self) -> None:
        req = ListSessionTemplatesRequest()
        assert req.all is False
        assert req.group_id is None

    def test_with_values(self) -> None:
        req = ListSessionTemplatesRequest(all=True, group_id="some-group-id")
        assert req.all is True
        assert req.group_id == "some-group-id"

    @pytest.mark.parametrize("alias", ["group_id", "groupId"])
    def test_group_id_alias(self, alias: str) -> None:
        req = ListSessionTemplatesRequest.model_validate({alias: "gid-123"})
        assert req.group_id == "gid-123"


class TestGetSessionTemplateRequest:
    def test_defaults(self) -> None:
        req = GetSessionTemplateRequest()
        assert req.format == "json"
        assert req.owner_access_key is None

    def test_yaml_format(self) -> None:
        req = GetSessionTemplateRequest(format="yaml")
        assert req.format == "yaml"

    def test_invalid_format_rejected(self) -> None:
        with pytest.raises(ValidationError):
            GetSessionTemplateRequest.model_validate({"format": "xml"})


class TestUpdateSessionTemplateRequest:
    def test_basic(self) -> None:
        req = UpdateSessionTemplateRequest(payload='{"template": {}}')
        assert req.group == "default"
        assert req.domain == "default"
        assert req.payload == '{"template": {}}'
        assert req.owner_access_key is None

    @pytest.mark.parametrize("alias", ["group", "groupName", "group_name"])
    def test_group_alias(self, alias: str) -> None:
        req = UpdateSessionTemplateRequest.model_validate({
            alias: "testgroup",
            "payload": "{}",
        })
        assert req.group == "testgroup"


class TestDeleteSessionTemplateRequest:
    def test_defaults(self) -> None:
        req = DeleteSessionTemplateRequest()
        assert req.owner_access_key is None

    def test_with_access_key(self) -> None:
        req = DeleteSessionTemplateRequest(owner_access_key="AKSOMEKEY")
        assert req.owner_access_key == "AKSOMEKEY"


class TestCreateClusterTemplateRequest:
    def test_with_defaults(self) -> None:
        req = CreateClusterTemplateRequest(payload='{"template": {}}')
        assert req.group == "default"
        assert req.domain == "default"
        assert req.owner_access_key is None

    @pytest.mark.parametrize("alias", ["group", "groupName", "group_name"])
    def test_group_alias(self, alias: str) -> None:
        req = CreateClusterTemplateRequest.model_validate({
            alias: "testgroup",
            "payload": "{}",
        })
        assert req.group == "testgroup"

    @pytest.mark.parametrize("alias", ["domain", "domainName", "domain_name"])
    def test_domain_alias(self, alias: str) -> None:
        req = CreateClusterTemplateRequest.model_validate({
            alias: "testdomain",
            "payload": "{}",
        })
        assert req.domain == "testdomain"


class TestListClusterTemplatesRequest:
    def test_defaults(self) -> None:
        req = ListClusterTemplatesRequest()
        assert req.all is False
        assert req.group_id is None

    @pytest.mark.parametrize("alias", ["group_id", "groupId"])
    def test_group_id_alias(self, alias: str) -> None:
        req = ListClusterTemplatesRequest.model_validate({alias: "gid-456"})
        assert req.group_id == "gid-456"


class TestGetClusterTemplateRequest:
    def test_defaults(self) -> None:
        req = GetClusterTemplateRequest()
        assert req.format == "yaml"
        assert req.owner_access_key is None

    def test_json_format(self) -> None:
        req = GetClusterTemplateRequest(format="json")
        assert req.format == "json"

    def test_invalid_format_rejected(self) -> None:
        with pytest.raises(ValidationError):
            GetClusterTemplateRequest.model_validate({"format": "toml"})


class TestUpdateClusterTemplateRequest:
    def test_basic(self) -> None:
        req = UpdateClusterTemplateRequest(payload='{"template": {}}')
        assert req.payload == '{"template": {}}'
        assert req.owner_access_key is None


class TestDeleteClusterTemplateRequest:
    def test_defaults(self) -> None:
        req = DeleteClusterTemplateRequest()
        assert req.owner_access_key is None


# --- Response DTO Tests ---


class TestSessionTemplateItemDTO:
    def test_instantiation(self) -> None:
        dto = SessionTemplateItemDTO(
            name="my-template",
            id="abc123",
            created_at=_NOW,
            is_owner=True,
            user="user-uuid",
            group="group-id",
            user_email="user@example.com",
            group_name="mygroup",
        )
        assert dto.name == "my-template"
        assert dto.id == "abc123"
        assert dto.created_at == _NOW
        assert dto.is_owner is True
        assert dto.user_email == "user@example.com"

    def test_nullable_fields(self) -> None:
        dto = SessionTemplateItemDTO(
            name="my-template",
            id="abc123",
            created_at=_NOW,
            is_owner=False,
            user=None,
            group=None,
            user_email=None,
            group_name=None,
        )
        assert dto.user is None
        assert dto.group is None
        assert dto.user_email is None
        assert dto.group_name is None


class TestSessionTemplateListItemDTO:
    def test_extends_base(self) -> None:
        dto = SessionTemplateListItemDTO(
            name="my-template",
            id="abc123",
            created_at=_NOW,
            is_owner=True,
            user="user-uuid",
            group="group-id",
            user_email="user@example.com",
            group_name="mygroup",
            domain_name="default",
            type="TASK",
            template={"key": "value"},
        )
        assert dto.domain_name == "default"
        assert dto.type == "TASK"
        assert dto.template == {"key": "value"}


class TestClusterTemplateListItemDTO:
    def test_with_type_user(self) -> None:
        dto = ClusterTemplateListItemDTO(
            name="cluster-template",
            id="def456",
            created_at=_NOW,
            is_owner=False,
            user="user-uuid",
            group="group-id",
            user_email=None,
            group_name="mygroup",
            type="user",
        )
        assert dto.type == "user"

    def test_with_type_group(self) -> None:
        dto = ClusterTemplateListItemDTO(
            name="cluster-template",
            id="def456",
            created_at=_NOW,
            is_owner=False,
            user=None,
            group="group-id",
            user_email=None,
            group_name="mygroup",
            type="group",
        )
        assert dto.type == "group"

    def test_invalid_type_rejected(self) -> None:
        with pytest.raises(ValidationError):
            ClusterTemplateListItemDTO.model_validate({
                "name": "cluster-template",
                "id": "def456",
                "created_at": _NOW.isoformat(),
                "is_owner": False,
                "user": "user-uuid",
                "group": "group-id",
                "user_email": None,
                "group_name": "mygroup",
                "type": "invalid",
            })


class TestCreateSessionTemplateResponse:
    def test_bare_list_input(self) -> None:
        raw = [
            {"id": "tmpl-1", "user": "user-1"},
            {"id": "tmpl-2", "user": "user-2"},
        ]
        resp = CreateSessionTemplateResponse.model_validate(raw)
        assert len(resp.root) == 2
        assert resp.root[0].id == "tmpl-1"
        assert resp.root[1].user == "user-2"

    def test_empty_list(self) -> None:
        resp = CreateSessionTemplateResponse.model_validate([])
        assert len(resp.root) == 0

    def test_serialization_roundtrip(self) -> None:
        raw = [{"id": "tmpl-1", "user": "user-1"}]
        resp = CreateSessionTemplateResponse.model_validate(raw)
        dumped = resp.model_dump()
        assert dumped == raw
        restored = CreateSessionTemplateResponse.model_validate(dumped)
        assert restored.root[0].id == "tmpl-1"


class TestListSessionTemplatesResponse:
    def test_bare_list_input(self) -> None:
        resp = ListSessionTemplatesResponse.model_validate([
            {
                "name": "tmpl",
                "id": "abc",
                "created_at": "2024-01-01T00:00:00Z",
                "is_owner": True,
                "user": "u1",
                "group": "g1",
                "user_email": "a@b.com",
                "group_name": "grp",
                "domain_name": "default",
                "type": "TASK",
                "template": {},
            },
        ])
        assert len(resp.root) == 1
        assert resp.root[0].name == "tmpl"


class TestGetSessionTemplateResponse:
    def test_instantiation(self) -> None:
        resp = GetSessionTemplateResponse(
            template={"metadata": {"name": "test"}},
            name="test",
            user_uuid="user-uuid",
            group_id="group-id",
            domain_name="default",
        )
        assert resp.name == "test"
        assert resp.template["metadata"]["name"] == "test"


class TestUpdateSessionTemplateResponse:
    def test_success(self) -> None:
        resp = UpdateSessionTemplateResponse(success=True)
        assert resp.success is True


class TestDeleteSessionTemplateResponse:
    def test_success(self) -> None:
        resp = DeleteSessionTemplateResponse(success=True)
        assert resp.success is True


class TestCreateClusterTemplateResponse:
    def test_instantiation(self) -> None:
        resp = CreateClusterTemplateResponse(id="tmpl-1", user="user-1")
        assert resp.id == "tmpl-1"
        assert resp.user == "user-1"


class TestListClusterTemplatesResponse:
    def test_bare_list_input(self) -> None:
        resp = ListClusterTemplatesResponse.model_validate([
            {
                "name": "cluster",
                "id": "abc",
                "created_at": "2024-01-01T00:00:00Z",
                "is_owner": True,
                "user": "u1",
                "group": "g1",
                "user_email": None,
                "group_name": "grp",
                "type": "group",
            },
        ])
        assert len(resp.root) == 1
        assert resp.root[0].type == "group"

    def test_serialization_roundtrip(self) -> None:
        raw = [
            {
                "name": "cluster",
                "id": "abc",
                "created_at": "2024-01-01T00:00:00Z",
                "is_owner": True,
                "user": "u1",
                "group": "g1",
                "user_email": None,
                "group_name": "grp",
                "type": "group",
            },
        ]
        resp = ListClusterTemplatesResponse.model_validate(raw)
        dumped = resp.model_dump()
        restored = ListClusterTemplatesResponse.model_validate(dumped)
        assert restored.root[0].name == "cluster"


class TestGetClusterTemplateResponse:
    def test_bare_dict_input(self) -> None:
        raw: dict[str, Any] = {"nodes": []}
        resp = GetClusterTemplateResponse.model_validate(raw)
        assert resp.root == {"nodes": []}
        assert resp.model_dump() == raw

    def test_serialization_roundtrip(self) -> None:
        raw: dict[str, Any] = {"nodes": []}
        resp = GetClusterTemplateResponse.model_validate(raw)
        dumped = resp.model_dump()
        assert dumped == raw
        restored = GetClusterTemplateResponse.model_validate(dumped)
        assert restored.root == {"nodes": []}


class TestUpdateClusterTemplateResponse:
    def test_success(self) -> None:
        resp = UpdateClusterTemplateResponse(success=True)
        assert resp.success is True


class TestDeleteClusterTemplateResponse:
    def test_success(self) -> None:
        resp = DeleteClusterTemplateResponse(success=True)
        assert resp.success is True


class TestModelDumpRoundTrip:
    """Test model_dump() and model_validate() round-trip for key models."""

    def test_create_session_request_round_trip(self) -> None:
        original = CreateSessionTemplateRequest(
            group="mygroup",
            domain="mydomain",
            owner_access_key="AKTEST",
            payload='{"template": {}}',
        )
        dumped = original.model_dump()
        restored = CreateSessionTemplateRequest.model_validate(dumped)
        assert restored.group == original.group
        assert restored.domain == original.domain
        assert restored.owner_access_key == original.owner_access_key
        assert restored.payload == original.payload

    def test_get_session_response_round_trip(self) -> None:
        original = GetSessionTemplateResponse(
            template={"metadata": {"name": "test"}},
            name="test",
            user_uuid="uuid-1",
            group_id="gid-1",
            domain_name="default",
        )
        dumped = original.model_dump()
        restored = GetSessionTemplateResponse.model_validate(dumped)
        assert restored.template == original.template
        assert restored.name == original.name
