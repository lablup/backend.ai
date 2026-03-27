"""Tests for ai.backend.common.dto.manager.v2.config.request module."""

from __future__ import annotations

import uuid

import pytest
from pydantic import ValidationError

from ai.backend.common.api_handlers import SENTINEL, Sentinel
from ai.backend.common.dto.manager.v2.config.request import (
    CreateDotfileInput,
    DeleteDotfileInput,
    UpdateBootstrapScriptInput,
    UpdateDotfileInput,
)
from ai.backend.common.dto.manager.v2.config.types import MAXIMUM_DOTFILE_SIZE, DotfileScope


class TestCreateDotfileInput:
    """Tests for CreateDotfileInput model creation and validation."""

    def test_valid_creation_with_required_fields(self) -> None:
        req = CreateDotfileInput(
            scope=DotfileScope.USER,
            path="/home/user/.bashrc",
            data="export PATH=$PATH:/usr/local/bin",
            permission="755",
        )
        assert req.scope == DotfileScope.USER
        assert req.path == "/home/user/.bashrc"
        assert req.data == "export PATH=$PATH:/usr/local/bin"
        assert req.permission == "755"
        assert req.domain is None
        assert req.group_id is None
        assert req.owner_access_key is None

    def test_valid_creation_with_all_fields(self) -> None:
        group_id = uuid.uuid4()
        req = CreateDotfileInput(
            scope=DotfileScope.GROUP,
            path="/etc/profile.d/custom.sh",
            data="echo 'Hello'",
            permission="644",
            domain="example.com",
            group_id=group_id,
            owner_access_key="AKIAIOSFODNN7EXAMPLE",
        )
        assert req.scope == DotfileScope.GROUP
        assert req.domain == "example.com"
        assert req.group_id == group_id
        assert req.owner_access_key == "AKIAIOSFODNN7EXAMPLE"

    def test_path_whitespace_is_stripped(self) -> None:
        req = CreateDotfileInput(
            scope=DotfileScope.USER,
            path="  /home/.bashrc  ",
            data="content",
            permission="644",
        )
        assert req.path == "/home/.bashrc"

    def test_blank_path_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            CreateDotfileInput(
                scope=DotfileScope.USER,
                path="   ",
                data="content",
                permission="644",
            )

    def test_empty_path_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            CreateDotfileInput(
                scope=DotfileScope.USER,
                path="",
                data="content",
                permission="644",
            )

    def test_data_exceeding_max_length_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            CreateDotfileInput(
                scope=DotfileScope.USER,
                path="/home/.bashrc",
                data="x" * (MAXIMUM_DOTFILE_SIZE + 1),
                permission="644",
            )

    def test_data_at_max_length_is_valid(self) -> None:
        req = CreateDotfileInput(
            scope=DotfileScope.USER,
            path="/home/.bashrc",
            data="x" * MAXIMUM_DOTFILE_SIZE,
            permission="644",
        )
        assert len(req.data) == MAXIMUM_DOTFILE_SIZE

    def test_invalid_permission_999_rejects(self) -> None:
        with pytest.raises(ValidationError):
            CreateDotfileInput(
                scope=DotfileScope.USER,
                path="/home/.bashrc",
                data="content",
                permission="999",
            )

    def test_invalid_permission_alpha_rejects(self) -> None:
        with pytest.raises(ValidationError):
            CreateDotfileInput(
                scope=DotfileScope.USER,
                path="/home/.bashrc",
                data="content",
                permission="abc",
            )

    def test_valid_domain_scope(self) -> None:
        req = CreateDotfileInput(
            scope=DotfileScope.DOMAIN,
            path="/etc/profile",
            data="export LANG=en_US.UTF-8",
            permission="644",
            domain="corp.example.com",
        )
        assert req.scope == DotfileScope.DOMAIN

    def test_group_id_from_uuid_string(self) -> None:
        group_id = uuid.uuid4()
        req = CreateDotfileInput.model_validate({
            "scope": "user",
            "path": "/home/.bashrc",
            "data": "content",
            "permission": "644",
            "group_id": str(group_id),
        })
        assert req.group_id == group_id

    def test_scope_from_string(self) -> None:
        req = CreateDotfileInput.model_validate({
            "scope": "group",
            "path": "/etc/profile",
            "data": "content",
            "permission": "755",
        })
        assert req.scope == DotfileScope.GROUP


class TestCreateDotfileInputRoundTrip:
    """Tests for CreateDotfileInput serialization round-trip."""

    def test_round_trip_with_required_fields(self) -> None:
        req = CreateDotfileInput(
            scope=DotfileScope.USER,
            path="/home/.bashrc",
            data="content",
            permission="755",
        )
        json_data = req.model_dump_json()
        restored = CreateDotfileInput.model_validate_json(json_data)
        assert restored.scope == req.scope
        assert restored.path == req.path
        assert restored.data == req.data
        assert restored.permission == req.permission
        assert restored.domain is None
        assert restored.group_id is None

    def test_round_trip_with_all_fields(self) -> None:
        group_id = uuid.uuid4()
        req = CreateDotfileInput(
            scope=DotfileScope.GROUP,
            path="/etc/profile",
            data="export LANG=en_US",
            permission="644",
            domain="example.com",
            group_id=group_id,
            owner_access_key="KEY123",
        )
        json_data = req.model_dump_json()
        restored = CreateDotfileInput.model_validate_json(json_data)
        assert restored.scope == req.scope
        assert restored.path == req.path
        assert restored.permission == req.permission
        assert restored.domain == req.domain
        assert restored.group_id == req.group_id
        assert restored.owner_access_key == req.owner_access_key


class TestUpdateDotfileInput:
    """Tests for UpdateDotfileInput model creation and validation."""

    def test_default_data_is_sentinel(self) -> None:
        req = UpdateDotfileInput(path="/home/.bashrc")
        assert req.data is SENTINEL
        assert isinstance(req.data, Sentinel)

    def test_explicit_sentinel_data(self) -> None:
        req = UpdateDotfileInput(path="/home/.bashrc", data=SENTINEL)
        assert req.data is SENTINEL

    def test_none_data_means_no_change(self) -> None:
        req = UpdateDotfileInput(path="/home/.bashrc", data=None)
        assert req.data is None

    def test_string_data_update(self) -> None:
        req = UpdateDotfileInput(path="/home/.bashrc", data="new content")
        assert req.data == "new content"

    def test_permission_update(self) -> None:
        req = UpdateDotfileInput(path="/home/.bashrc", permission="755")
        assert req.permission == "755"

    def test_permission_default_is_none(self) -> None:
        req = UpdateDotfileInput(path="/home/.bashrc")
        assert req.permission is None

    def test_path_whitespace_is_stripped(self) -> None:
        req = UpdateDotfileInput(path="  /home/.bashrc  ")
        assert req.path == "/home/.bashrc"

    def test_blank_path_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            UpdateDotfileInput(path="   ")

    def test_empty_path_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            UpdateDotfileInput(path="")

    def test_invalid_permission_rejects(self) -> None:
        with pytest.raises(ValidationError):
            UpdateDotfileInput(path="/home/.bashrc", permission="999")

    def test_partial_update_data_only(self) -> None:
        req = UpdateDotfileInput(path="/home/.bashrc", data="updated content")
        assert req.data == "updated content"
        assert req.permission is None

    def test_partial_update_permission_only(self) -> None:
        req = UpdateDotfileInput(path="/home/.bashrc", permission="644")
        assert req.data is SENTINEL
        assert req.permission == "644"


class TestUpdateDotfileInputRoundTrip:
    """Tests for UpdateDotfileInput serialization round-trip (non-SENTINEL values)."""

    def test_round_trip_with_string_data(self) -> None:
        req = UpdateDotfileInput(path="/home/.bashrc", data="new content", permission="644")
        json_data = req.model_dump_json()
        restored = UpdateDotfileInput.model_validate_json(json_data)
        assert restored.path == req.path
        assert restored.data == "new content"
        assert restored.permission == "644"

    def test_round_trip_with_none_data(self) -> None:
        req = UpdateDotfileInput(path="/home/.bashrc", data=None, permission=None)
        json_data = req.model_dump_json()
        restored = UpdateDotfileInput.model_validate_json(json_data)
        assert restored.path == req.path
        assert restored.data is None
        assert restored.permission is None


class TestDeleteDotfileInput:
    """Tests for DeleteDotfileInput model creation and validation."""

    def test_valid_creation(self) -> None:
        req = DeleteDotfileInput(path="/home/.bashrc")
        assert req.path == "/home/.bashrc"

    def test_path_whitespace_is_stripped(self) -> None:
        req = DeleteDotfileInput(path="  /home/.bashrc  ")
        assert req.path == "/home/.bashrc"

    def test_blank_path_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            DeleteDotfileInput(path="   ")

    def test_empty_path_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            DeleteDotfileInput(path="")

    def test_missing_path_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            DeleteDotfileInput.model_validate({})

    def test_round_trip(self) -> None:
        req = DeleteDotfileInput(path="/home/.vimrc")
        json_data = req.model_dump_json()
        restored = DeleteDotfileInput.model_validate_json(json_data)
        assert restored.path == req.path


class TestUpdateBootstrapScriptInput:
    """Tests for UpdateBootstrapScriptInput model creation and validation."""

    def test_valid_creation(self) -> None:
        req = UpdateBootstrapScriptInput(script="#!/bin/bash\necho hello")
        assert req.script == "#!/bin/bash\necho hello"

    def test_empty_script_is_valid(self) -> None:
        req = UpdateBootstrapScriptInput(script="")
        assert req.script == ""

    def test_script_exceeding_max_length_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            UpdateBootstrapScriptInput(script="x" * (MAXIMUM_DOTFILE_SIZE + 1))

    def test_script_at_max_length_is_valid(self) -> None:
        req = UpdateBootstrapScriptInput(script="x" * MAXIMUM_DOTFILE_SIZE)
        assert len(req.script) == MAXIMUM_DOTFILE_SIZE

    def test_round_trip(self) -> None:
        req = UpdateBootstrapScriptInput(script="#!/bin/bash\nexport PATH=$PATH:/usr/local/bin")
        json_data = req.model_dump_json()
        restored = UpdateBootstrapScriptInput.model_validate_json(json_data)
        assert restored.script == req.script
