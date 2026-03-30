"""Tests for ai.backend.common.dto.manager.v2.etcd.request module."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from ai.backend.common.dto.manager.v2.etcd.request import (
    DeleteConfigInput,
    GetConfigInput,
    GetResourceMetadataInput,
    SetConfigInput,
)


class TestGetConfigInput:
    """Tests for GetConfigInput model creation and validation."""

    def test_valid_creation_with_key(self) -> None:
        req = GetConfigInput(key="/config/backend")
        assert req.key == "/config/backend"
        assert req.prefix is False

    def test_prefix_defaults_to_false(self) -> None:
        req = GetConfigInput(key="some/key")
        assert req.prefix is False

    def test_prefix_can_be_true(self) -> None:
        req = GetConfigInput(key="/config/", prefix=True)
        assert req.prefix is True

    def test_key_whitespace_is_stripped(self) -> None:
        req = GetConfigInput(key="  /config/key  ")
        assert req.key == "/config/key"

    def test_blank_key_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            GetConfigInput(key="   ")

    def test_empty_key_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            GetConfigInput(key="")

    def test_missing_key_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            GetConfigInput.model_validate({})

    def test_round_trip(self) -> None:
        req = GetConfigInput(key="/config/backend", prefix=True)
        json_data = req.model_dump_json()
        restored = GetConfigInput.model_validate_json(json_data)
        assert restored.key == req.key
        assert restored.prefix == req.prefix

    def test_round_trip_with_default_prefix(self) -> None:
        req = GetConfigInput(key="/config/backend")
        json_data = req.model_dump_json()
        restored = GetConfigInput.model_validate_json(json_data)
        assert restored.key == req.key
        assert restored.prefix is False


class TestSetConfigInput:
    """Tests for SetConfigInput model creation and validation."""

    def test_valid_creation_with_string_value(self) -> None:
        req = SetConfigInput(key="/config/foo", value="bar")
        assert req.key == "/config/foo"
        assert req.value == "bar"

    def test_value_can_be_integer(self) -> None:
        req = SetConfigInput(key="/config/count", value=42)
        assert req.value == 42

    def test_value_can_be_dict(self) -> None:
        req = SetConfigInput(key="/config/nested", value={"a": 1, "b": "two"})
        assert req.value == {"a": 1, "b": "two"}

    def test_value_can_be_list(self) -> None:
        req = SetConfigInput(key="/config/list", value=["x", "y", "z"])
        assert req.value == ["x", "y", "z"]

    def test_value_can_be_none(self) -> None:
        req = SetConfigInput(key="/config/null", value=None)
        assert req.value is None

    def test_value_can_be_bool(self) -> None:
        req = SetConfigInput(key="/config/enabled", value=True)
        assert req.value is True

    def test_key_whitespace_is_stripped(self) -> None:
        req = SetConfigInput(key="  /config/key  ", value="val")
        assert req.key == "/config/key"

    def test_blank_key_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            SetConfigInput(key="   ", value="val")

    def test_empty_key_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            SetConfigInput(key="", value="val")

    def test_round_trip_with_string_value(self) -> None:
        req = SetConfigInput(key="/config/backend", value="enabled")
        json_data = req.model_dump_json()
        restored = SetConfigInput.model_validate_json(json_data)
        assert restored.key == req.key
        assert restored.value == req.value

    def test_round_trip_with_nested_dict_value(self) -> None:
        req = SetConfigInput(key="/config/nested", value={"level": 1, "items": ["a", "b"]})
        json_data = req.model_dump_json()
        restored = SetConfigInput.model_validate_json(json_data)
        assert restored.key == req.key
        assert restored.value == {"level": 1, "items": ["a", "b"]}


class TestDeleteConfigInput:
    """Tests for DeleteConfigInput model creation and validation."""

    def test_valid_creation_with_key(self) -> None:
        req = DeleteConfigInput(key="/config/backend")
        assert req.key == "/config/backend"
        assert req.prefix is False

    def test_prefix_defaults_to_false(self) -> None:
        req = DeleteConfigInput(key="some/key")
        assert req.prefix is False

    def test_prefix_can_be_true(self) -> None:
        req = DeleteConfigInput(key="/config/", prefix=True)
        assert req.prefix is True

    def test_key_whitespace_is_stripped(self) -> None:
        req = DeleteConfigInput(key="  /config/key  ")
        assert req.key == "/config/key"

    def test_blank_key_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            DeleteConfigInput(key="   ")

    def test_empty_key_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            DeleteConfigInput(key="")

    def test_missing_key_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            DeleteConfigInput.model_validate({})

    def test_round_trip(self) -> None:
        req = DeleteConfigInput(key="/config/backend", prefix=True)
        json_data = req.model_dump_json()
        restored = DeleteConfigInput.model_validate_json(json_data)
        assert restored.key == req.key
        assert restored.prefix == req.prefix


class TestGetResourceMetadataInput:
    """Tests for GetResourceMetadataInput model creation and validation."""

    def test_default_sgroup_is_none(self) -> None:
        req = GetResourceMetadataInput()
        assert req.sgroup is None

    def test_sgroup_can_be_set(self) -> None:
        req = GetResourceMetadataInput(sgroup="gpu-group")
        assert req.sgroup == "gpu-group"

    def test_sgroup_can_be_none_explicitly(self) -> None:
        req = GetResourceMetadataInput(sgroup=None)
        assert req.sgroup is None

    def test_round_trip_with_none(self) -> None:
        req = GetResourceMetadataInput()
        json_data = req.model_dump_json()
        restored = GetResourceMetadataInput.model_validate_json(json_data)
        assert restored.sgroup is None

    def test_round_trip_with_sgroup(self) -> None:
        req = GetResourceMetadataInput(sgroup="cpu-group")
        json_data = req.model_dump_json()
        restored = GetResourceMetadataInput.model_validate_json(json_data)
        assert restored.sgroup == "cpu-group"
