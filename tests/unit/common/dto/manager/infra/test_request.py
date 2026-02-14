"""
Unit tests for Infrastructure request DTOs.
"""

from __future__ import annotations

import uuid

import pytest
from pydantic import BaseModel, ValidationError

from ai.backend.common.dto.manager.infra.request import (
    CheckPresetsRequest,
    DeleteConfigRequest,
    GetConfigRequest,
    GetResourceMetadataRequest,
    GetWSProxyVersionRequest,
    ListPresetsRequest,
    ListScalingGroupsRequest,
    SetConfigRequest,
    UsagePerMonthRequest,
    UsagePerPeriodRequest,
    WatcherAgentRequest,
)

# --- etcd requests ---


class TestGetResourceMetadataRequest:
    def test_default_sgroup_is_none(self) -> None:
        req = GetResourceMetadataRequest()
        assert req.sgroup is None

    def test_with_sgroup(self) -> None:
        req = GetResourceMetadataRequest(sgroup="my-scaling-group")
        assert req.sgroup == "my-scaling-group"

    def test_serialization_roundtrip(self) -> None:
        req = GetResourceMetadataRequest(sgroup="sg1")
        json_str = req.model_dump_json()
        restored = GetResourceMetadataRequest.model_validate_json(json_str)
        assert restored.sgroup == req.sgroup


class TestGetConfigRequest:
    def test_valid(self) -> None:
        req = GetConfigRequest(key="config/some/key")
        assert req.key == "config/some/key"
        assert req.prefix is False

    def test_with_prefix(self) -> None:
        req = GetConfigRequest(key="config/", prefix=True)
        assert req.prefix is True

    def test_missing_key_raises(self) -> None:
        with pytest.raises(ValidationError):
            GetConfigRequest()  # type: ignore[call-arg]

    def test_serialization_roundtrip(self) -> None:
        req = GetConfigRequest(key="a/b", prefix=True)
        json_str = req.model_dump_json()
        restored = GetConfigRequest.model_validate_json(json_str)
        assert restored.key == req.key
        assert restored.prefix == req.prefix


class TestSetConfigRequest:
    def test_scalar_value(self) -> None:
        req = SetConfigRequest(key="config/key", value="hello")
        assert req.value == "hello"

    def test_dict_value(self) -> None:
        req = SetConfigRequest(key="config/key", value={"nested": "data"})
        assert req.value == {"nested": "data"}

    def test_missing_key_raises(self) -> None:
        with pytest.raises(ValidationError):
            SetConfigRequest(value="val")  # type: ignore[call-arg]


class TestDeleteConfigRequest:
    def test_valid(self) -> None:
        req = DeleteConfigRequest(key="config/key")
        assert req.key == "config/key"
        assert req.prefix is False

    def test_with_prefix(self) -> None:
        req = DeleteConfigRequest(key="config/", prefix=True)
        assert req.prefix is True


# --- scaling_group requests ---


class TestListScalingGroupsRequest:
    def test_with_string_group(self) -> None:
        req = ListScalingGroupsRequest(group="my-group")
        assert req.group == "my-group"

    def test_with_uuid_group(self) -> None:
        gid = uuid.uuid4()
        req = ListScalingGroupsRequest(group=gid)
        assert req.group == gid

    def test_alias_group_id(self) -> None:
        req = ListScalingGroupsRequest.model_validate({"group_id": "alias-test"})
        assert req.group == "alias-test"

    def test_alias_group_name(self) -> None:
        req = ListScalingGroupsRequest.model_validate({"group_name": "alias-test2"})
        assert req.group == "alias-test2"

    def test_missing_group_raises(self) -> None:
        with pytest.raises(ValidationError):
            ListScalingGroupsRequest()  # type: ignore[call-arg]


class TestGetWSProxyVersionRequest:
    def test_default_group_is_none(self) -> None:
        req = GetWSProxyVersionRequest()
        assert req.group is None

    def test_with_group(self) -> None:
        req = GetWSProxyVersionRequest(group="my-group")
        assert req.group == "my-group"

    def test_alias_group_id(self) -> None:
        req = GetWSProxyVersionRequest.model_validate({"group_id": "g1"})
        assert req.group == "g1"


# --- resource requests ---


class TestListPresetsRequest:
    def test_default_scaling_group_is_none(self) -> None:
        req = ListPresetsRequest()
        assert req.scaling_group is None

    def test_with_scaling_group(self) -> None:
        req = ListPresetsRequest(scaling_group="sg1")
        assert req.scaling_group == "sg1"


class TestCheckPresetsRequest:
    def test_valid(self) -> None:
        req = CheckPresetsRequest(group="my-group")
        assert req.group == "my-group"
        assert req.scaling_group is None

    def test_with_scaling_group(self) -> None:
        req = CheckPresetsRequest(group="g1", scaling_group="sg1")
        assert req.scaling_group == "sg1"

    def test_missing_group_raises(self) -> None:
        with pytest.raises(ValidationError):
            CheckPresetsRequest()  # type: ignore[call-arg]


class TestUsagePerMonthRequest:
    def test_valid(self) -> None:
        req = UsagePerMonthRequest(month="202006")
        assert req.month == "202006"
        assert req.group_ids is None

    def test_with_group_ids(self) -> None:
        req = UsagePerMonthRequest(group_ids=["g1", "g2"], month="202106")
        assert req.group_ids == ["g1", "g2"]

    def test_invalid_month_pattern(self) -> None:
        with pytest.raises(ValidationError):
            UsagePerMonthRequest(month="abc")

    def test_serialization_roundtrip(self) -> None:
        req = UsagePerMonthRequest(group_ids=["g1"], month="202312")
        json_str = req.model_dump_json()
        restored = UsagePerMonthRequest.model_validate_json(json_str)
        assert restored.month == req.month
        assert restored.group_ids == req.group_ids


class TestUsagePerPeriodRequest:
    def test_valid(self) -> None:
        req = UsagePerPeriodRequest(start_date="20200601", end_date="20200630")
        assert req.start_date == "20200601"
        assert req.end_date == "20200630"
        assert req.project_id is None

    def test_with_project_id(self) -> None:
        req = UsagePerPeriodRequest(project_id="p1", start_date="20200601", end_date="20200630")
        assert req.project_id == "p1"

    def test_alias_group_id(self) -> None:
        req = UsagePerPeriodRequest.model_validate({
            "group_id": "g1",
            "start_date": "20200601",
            "end_date": "20200630",
        })
        assert req.project_id == "g1"

    def test_invalid_start_date_pattern(self) -> None:
        with pytest.raises(ValidationError):
            UsagePerPeriodRequest(start_date="2020-06-01", end_date="20200630")

    def test_invalid_end_date_pattern(self) -> None:
        with pytest.raises(ValidationError):
            UsagePerPeriodRequest(start_date="20200601", end_date="short")


class TestWatcherAgentRequest:
    def test_valid(self) -> None:
        req = WatcherAgentRequest(agent_id="i-agent001")
        assert req.agent_id == "i-agent001"

    def test_alias_agent(self) -> None:
        req = WatcherAgentRequest.model_validate({"agent": "i-agent002"})
        assert req.agent_id == "i-agent002"

    def test_missing_agent_id_raises(self) -> None:
        with pytest.raises(ValidationError):
            WatcherAgentRequest()  # type: ignore[call-arg]

    def test_serialization_roundtrip(self) -> None:
        req = WatcherAgentRequest(agent_id="i-agent003")
        json_str = req.model_dump_json()
        restored = WatcherAgentRequest.model_validate_json(json_str)
        assert restored.agent_id == req.agent_id


class TestFieldDescriptions:
    """Verify all request models have descriptions for their fields."""

    @pytest.mark.parametrize(
        "model_cls",
        [
            GetResourceMetadataRequest,
            GetConfigRequest,
            SetConfigRequest,
            DeleteConfigRequest,
            ListScalingGroupsRequest,
            GetWSProxyVersionRequest,
            ListPresetsRequest,
            CheckPresetsRequest,
            UsagePerMonthRequest,
            UsagePerPeriodRequest,
            WatcherAgentRequest,
        ],
    )
    def test_all_fields_have_descriptions(self, model_cls: type[BaseModel]) -> None:
        schema = model_cls.model_json_schema()
        properties = schema.get("properties", {})
        for field_name, field_schema in properties.items():
            assert "description" in field_schema, (
                f"{model_cls.__name__}.{field_name} is missing a description"
            )
