"""
Unit tests for config (dotfile) DTO models.
"""

from __future__ import annotations

from uuid import UUID

import pytest
from pydantic import ValidationError

from ai.backend.common.dto.manager.config.request import (
    CreateDomainDotfileRequest,
    CreateGroupDotfileRequest,
    CreateUserDotfileRequest,
    DeleteDomainDotfileRequest,
    DeleteGroupDotfileRequest,
    DeleteUserDotfileRequest,
    GetBootstrapScriptRequest,
    GetDomainDotfileRequest,
    GetGroupDotfileRequest,
    GetUserDotfileRequest,
    UpdateBootstrapScriptRequest,
    UpdateDomainDotfileRequest,
    UpdateGroupDotfileRequest,
    UpdateUserDotfileRequest,
)
from ai.backend.common.dto.manager.config.response import (
    CreateDotfileResponse,
    DeleteDotfileResponse,
    DotfileItem,
    GetBootstrapScriptResponse,
    GetDotfileResponse,
    ListDotfilesResponse,
    UpdateBootstrapScriptResponse,
    UpdateDotfileResponse,
)
from ai.backend.common.dto.manager.config.types import MAXIMUM_DOTFILE_SIZE

# ---- DotfilePermission validation ----


class TestDotfilePermission:
    def test_valid_permission(self) -> None:
        req = CreateUserDotfileRequest(
            path=".bashrc",
            data="export FOO=bar",
            permission="755",
        )
        assert req.permission == "755"

    @pytest.mark.parametrize("perm", ["644", "777", "000", "421"])
    def test_valid_permission_variants(self, perm: str) -> None:
        req = CreateUserDotfileRequest(
            path=".bashrc",
            data="content",
            permission=perm,
        )
        assert req.permission == perm

    @pytest.mark.parametrize("perm", ["999", "abc", "12", "7777", "8", ""])
    def test_invalid_permission(self, perm: str) -> None:
        with pytest.raises(ValidationError):
            CreateUserDotfileRequest(
                path=".bashrc",
                data="content",
                permission=perm,
            )


# ---- max_length constraint ----


class TestMaxLength:
    def test_data_within_limit(self) -> None:
        req = CreateUserDotfileRequest(
            path=".bashrc",
            data="x" * 100,
            permission="644",
        )
        assert len(req.data) == 100

    def test_data_exceeds_limit(self) -> None:
        with pytest.raises(ValidationError):
            CreateUserDotfileRequest(
                path=".bashrc",
                data="x" * (MAXIMUM_DOTFILE_SIZE + 1),
                permission="644",
            )

    def test_bootstrap_script_exceeds_limit(self) -> None:
        with pytest.raises(ValidationError):
            UpdateBootstrapScriptRequest(
                script="x" * (MAXIMUM_DOTFILE_SIZE + 1),
            )


# ---- User Config Request models ----


class TestUserConfigRequests:
    def test_create_user_dotfile(self) -> None:
        req = CreateUserDotfileRequest(
            path=".bashrc",
            data="export PATH=$PATH:/usr/local/bin",
            permission="644",
            owner_access_key="AKIAIOSFODNN7EXAMPLE",
        )
        assert req.path == ".bashrc"
        assert req.permission == "644"
        assert req.owner_access_key == "AKIAIOSFODNN7EXAMPLE"

    def test_create_user_dotfile_without_owner(self) -> None:
        req = CreateUserDotfileRequest(
            path=".vimrc",
            data="set number",
            permission="644",
        )
        assert req.owner_access_key is None

    def test_get_user_dotfile_with_path(self) -> None:
        req = GetUserDotfileRequest(path=".bashrc")
        assert req.path == ".bashrc"
        assert req.owner_access_key is None

    def test_get_user_dotfile_list_all(self) -> None:
        req = GetUserDotfileRequest()
        assert req.path is None
        assert req.owner_access_key is None

    def test_update_user_dotfile(self) -> None:
        req = UpdateUserDotfileRequest(
            path=".bashrc",
            data="updated content",
            permission="755",
        )
        assert req.path == ".bashrc"
        assert req.data == "updated content"

    def test_delete_user_dotfile(self) -> None:
        req = DeleteUserDotfileRequest(path=".bashrc")
        assert req.path == ".bashrc"

    def test_update_bootstrap_script(self) -> None:
        req = UpdateBootstrapScriptRequest(script="#!/bin/bash\necho hello")
        assert req.script == "#!/bin/bash\necho hello"

    def test_get_bootstrap_script(self) -> None:
        req = GetBootstrapScriptRequest()
        assert req is not None

    def test_create_user_dotfile_serialization_roundtrip(self) -> None:
        req = CreateUserDotfileRequest(
            path=".profile",
            data="source ~/.bashrc",
            permission="644",
            owner_access_key="TESTKEY",
        )
        json_data = req.model_dump_json()
        restored = CreateUserDotfileRequest.model_validate_json(json_data)
        assert restored.path == req.path
        assert restored.data == req.data
        assert restored.permission == req.permission
        assert restored.owner_access_key == req.owner_access_key


# ---- Group Config Request models ----


class TestGroupConfigRequests:
    def test_create_group_dotfile_with_uuid(self) -> None:
        group_uuid = UUID("550e8400-e29b-41d4-a716-446655440000")
        req = CreateGroupDotfileRequest(
            group=group_uuid,
            path=".bashrc",
            data="content",
            permission="644",
        )
        assert req.group == group_uuid

    def test_create_group_dotfile_with_name(self) -> None:
        req = CreateGroupDotfileRequest(
            group="my-group",
            domain="default",
            path=".bashrc",
            data="content",
            permission="644",
        )
        assert req.group == "my-group"
        assert req.domain == "default"

    def test_group_alias_groupId(self) -> None:
        req = CreateGroupDotfileRequest.model_validate({
            "groupId": "550e8400-e29b-41d4-a716-446655440000",
            "path": ".bashrc",
            "data": "content",
            "permission": "644",
        })
        assert str(req.group) == "550e8400-e29b-41d4-a716-446655440000"

    def test_group_alias_group_id(self) -> None:
        req = CreateGroupDotfileRequest.model_validate({
            "group_id": "my-group",
            "path": ".bashrc",
            "data": "content",
            "permission": "644",
        })
        assert req.group == "my-group"

    def test_group_alias_group(self) -> None:
        req = CreateGroupDotfileRequest.model_validate({
            "group": "my-group",
            "path": ".bashrc",
            "data": "content",
            "permission": "644",
        })
        assert req.group == "my-group"

    def test_get_group_dotfile_list_all(self) -> None:
        req = GetGroupDotfileRequest(group="my-group")
        assert req.path is None
        assert req.domain is None

    def test_update_group_dotfile(self) -> None:
        req = UpdateGroupDotfileRequest(
            group="my-group",
            domain="default",
            path=".bashrc",
            data="updated",
            permission="755",
        )
        assert req.data == "updated"

    def test_delete_group_dotfile(self) -> None:
        req = DeleteGroupDotfileRequest(
            group="my-group",
            path=".bashrc",
        )
        assert req.path == ".bashrc"

    def test_create_group_dotfile_serialization_roundtrip(self) -> None:
        req = CreateGroupDotfileRequest(
            group="my-group",
            domain="default",
            path=".profile",
            data="content",
            permission="644",
        )
        json_data = req.model_dump_json()
        restored = CreateGroupDotfileRequest.model_validate_json(json_data)
        assert restored.group == req.group
        assert restored.domain == req.domain
        assert restored.path == req.path


# ---- Domain Config Request models ----


class TestDomainConfigRequests:
    def test_create_domain_dotfile(self) -> None:
        req = CreateDomainDotfileRequest(
            domain="default",
            path=".bashrc",
            data="content",
            permission="644",
        )
        assert req.domain == "default"
        assert req.path == ".bashrc"

    def test_get_domain_dotfile_with_path(self) -> None:
        req = GetDomainDotfileRequest(domain="default", path=".bashrc")
        assert req.path == ".bashrc"

    def test_get_domain_dotfile_list_all(self) -> None:
        req = GetDomainDotfileRequest(domain="default")
        assert req.path is None

    def test_update_domain_dotfile(self) -> None:
        req = UpdateDomainDotfileRequest(
            domain="default",
            path=".bashrc",
            data="updated",
            permission="755",
        )
        assert req.data == "updated"

    def test_delete_domain_dotfile(self) -> None:
        req = DeleteDomainDotfileRequest(domain="default", path=".bashrc")
        assert req.path == ".bashrc"

    def test_create_domain_dotfile_serialization_roundtrip(self) -> None:
        req = CreateDomainDotfileRequest(
            domain="default",
            path=".profile",
            data="content",
            permission="644",
        )
        json_data = req.model_dump_json()
        restored = CreateDomainDotfileRequest.model_validate_json(json_data)
        assert restored.domain == req.domain
        assert restored.path == req.path
        assert restored.permission == req.permission


# ---- Response models ----


class TestResponseModels:
    def test_dotfile_item(self) -> None:
        item = DotfileItem(path=".bashrc", perm="644", data="content")
        assert item.path == ".bashrc"
        assert item.perm == "644"

    def test_create_dotfile_response(self) -> None:
        resp = CreateDotfileResponse()
        assert resp.model_dump() == {}

    def test_update_dotfile_response(self) -> None:
        resp = UpdateDotfileResponse()
        assert resp.model_dump() == {}

    def test_delete_dotfile_response(self) -> None:
        resp = DeleteDotfileResponse(success=True)
        assert resp.success is True

    def test_get_dotfile_response(self) -> None:
        resp = GetDotfileResponse(path=".bashrc", perm="644", data="content")
        assert resp.path == ".bashrc"
        assert resp.perm == "644"

    def test_list_dotfiles_response(self) -> None:
        items = [
            DotfileItem(path=".bashrc", perm="644", data="content1"),
            DotfileItem(path=".vimrc", perm="755", data="content2"),
        ]
        resp = ListDotfilesResponse(items=items)
        assert len(resp.items) == 2
        assert resp.items[0].path == ".bashrc"
        assert resp.items[1].path == ".vimrc"

    def test_get_bootstrap_script_response(self) -> None:
        resp = GetBootstrapScriptResponse(script="#!/bin/bash\necho hello")
        assert resp.script == "#!/bin/bash\necho hello"

    def test_update_bootstrap_script_response(self) -> None:
        resp = UpdateBootstrapScriptResponse()
        assert resp.model_dump() == {}

    def test_delete_dotfile_response_serialization_roundtrip(self) -> None:
        resp = DeleteDotfileResponse(success=True)
        json_data = resp.model_dump_json()
        restored = DeleteDotfileResponse.model_validate_json(json_data)
        assert restored.success == resp.success

    def test_list_dotfiles_response_serialization_roundtrip(self) -> None:
        items = [DotfileItem(path=".bashrc", perm="644", data="content")]
        resp = ListDotfilesResponse(items=items)
        json_data = resp.model_dump_json()
        restored = ListDotfilesResponse.model_validate_json(json_data)
        assert len(restored.items) == 1
        assert restored.items[0].path == ".bashrc"


# ---- Field descriptions ----


class TestFieldDescriptions:
    def test_request_fields_have_descriptions(self) -> None:
        schema = CreateUserDotfileRequest.model_json_schema()
        props = schema["properties"]
        for field_name in ("path", "data", "permission"):
            assert "description" in props[field_name], f"Field '{field_name}' missing description"

    def test_response_fields_have_descriptions(self) -> None:
        schema = GetDotfileResponse.model_json_schema()
        props = schema["properties"]
        for field_name in ("path", "perm", "data"):
            assert "description" in props[field_name], f"Field '{field_name}' missing description"

    def test_dotfile_item_fields_have_descriptions(self) -> None:
        schema = DotfileItem.model_json_schema()
        props = schema["properties"]
        for field_name in ("path", "perm", "data"):
            assert "description" in props[field_name], f"Field '{field_name}' missing description"
