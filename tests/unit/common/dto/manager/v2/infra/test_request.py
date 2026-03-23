"""Tests for ai.backend.common.dto.manager.v2.infra.request module."""

from __future__ import annotations

import uuid

import pytest
from pydantic import ValidationError

from ai.backend.common.dto.manager.v2.infra.request import (
    CheckPresetsInput,
    GetWSProxyVersionInput,
    ListPresetsInput,
    ListScalingGroupsInput,
    UsagePerMonthInput,
    UsagePerPeriodInput,
    WatcherAgentInput,
)


class TestListScalingGroupsInput:
    """Tests for ListScalingGroupsInput model."""

    def test_accepts_string_group(self) -> None:
        req = ListScalingGroupsInput(group="default")
        assert req.group == "default"

    def test_accepts_uuid_group(self) -> None:
        group_id = uuid.uuid4()
        req = ListScalingGroupsInput(group=group_id)
        assert req.group == group_id

    def test_accepts_uuid_string_as_group(self) -> None:
        group_id = uuid.uuid4()
        req = ListScalingGroupsInput.model_validate({"group": str(group_id)})
        # str | UUID union: string input remains a string
        assert req.group == str(group_id)

    def test_accepts_group_via_group_id_alias(self) -> None:
        group_id = uuid.uuid4()
        req = ListScalingGroupsInput.model_validate({"group_id": group_id})
        assert req.group == group_id

    def test_accepts_group_via_group_name_alias(self) -> None:
        req = ListScalingGroupsInput.model_validate({"group_name": "my-group"})
        assert req.group == "my-group"

    def test_missing_group_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            ListScalingGroupsInput.model_validate({})

    def test_group_as_uuid_instance(self) -> None:
        group_id = uuid.uuid4()
        req = ListScalingGroupsInput(group=group_id)
        assert isinstance(req.group, uuid.UUID)

    def test_group_as_str_instance(self) -> None:
        req = ListScalingGroupsInput(group="my-group")
        assert isinstance(req.group, str)


class TestGetWSProxyVersionInput:
    """Tests for GetWSProxyVersionInput model."""

    def test_default_group_is_none(self) -> None:
        req = GetWSProxyVersionInput()
        assert req.group is None

    def test_accepts_string_group(self) -> None:
        req = GetWSProxyVersionInput(group="default")
        assert req.group == "default"

    def test_accepts_uuid_group(self) -> None:
        group_id = uuid.uuid4()
        req = GetWSProxyVersionInput(group=group_id)
        assert req.group == group_id

    def test_accepts_none_group(self) -> None:
        req = GetWSProxyVersionInput(group=None)
        assert req.group is None

    def test_accepts_group_via_group_id_alias(self) -> None:
        group_id = uuid.uuid4()
        req = GetWSProxyVersionInput.model_validate({"group_id": group_id})
        assert req.group == group_id

    def test_accepts_group_via_group_name_alias(self) -> None:
        req = GetWSProxyVersionInput.model_validate({"group_name": "scaling-group"})
        assert req.group == "scaling-group"


class TestListPresetsInput:
    """Tests for ListPresetsInput model."""

    def test_default_scaling_group_is_none(self) -> None:
        req = ListPresetsInput()
        assert req.scaling_group is None

    def test_accepts_scaling_group_string(self) -> None:
        req = ListPresetsInput(scaling_group="gpu-cluster")
        assert req.scaling_group == "gpu-cluster"

    def test_accepts_none_scaling_group(self) -> None:
        req = ListPresetsInput(scaling_group=None)
        assert req.scaling_group is None


class TestCheckPresetsInput:
    """Tests for CheckPresetsInput model."""

    def test_valid_creation_with_required_group(self) -> None:
        req = CheckPresetsInput(group="research")
        assert req.group == "research"
        assert req.scaling_group is None

    def test_valid_creation_with_all_fields(self) -> None:
        req = CheckPresetsInput(group="research", scaling_group="gpu-cluster")
        assert req.group == "research"
        assert req.scaling_group == "gpu-cluster"

    def test_missing_group_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            CheckPresetsInput.model_validate({})

    def test_default_scaling_group_is_none(self) -> None:
        req = CheckPresetsInput(group="default")
        assert req.scaling_group is None

    def test_accepts_none_scaling_group(self) -> None:
        req = CheckPresetsInput(group="default", scaling_group=None)
        assert req.scaling_group is None


class TestUsagePerMonthInput:
    """Tests for UsagePerMonthInput model."""

    def test_valid_month_format(self) -> None:
        req = UsagePerMonthInput(month="202006")
        assert req.month == "202006"

    def test_valid_month_format_recent(self) -> None:
        req = UsagePerMonthInput(month="202312")
        assert req.month == "202312"

    def test_default_group_ids_is_none(self) -> None:
        req = UsagePerMonthInput(month="202006")
        assert req.group_ids is None

    def test_accepts_group_ids_list(self) -> None:
        req = UsagePerMonthInput(month="202006", group_ids=["g1", "g2"])
        assert req.group_ids == ["g1", "g2"]

    def test_invalid_month_too_short_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            UsagePerMonthInput(month="20200")

    def test_invalid_month_too_long_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            UsagePerMonthInput(month="2020060")

    def test_invalid_month_with_letters_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            UsagePerMonthInput(month="2020AB")

    def test_invalid_month_with_dashes_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            UsagePerMonthInput(month="2020-06")

    def test_missing_month_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            UsagePerMonthInput.model_validate({})


class TestUsagePerPeriodInput:
    """Tests for UsagePerPeriodInput model."""

    def test_valid_date_formats(self) -> None:
        req = UsagePerPeriodInput(start_date="20200601", end_date="20200630")
        assert req.start_date == "20200601"
        assert req.end_date == "20200630"

    def test_default_project_id_is_none(self) -> None:
        req = UsagePerPeriodInput(start_date="20200601", end_date="20200630")
        assert req.project_id is None

    def test_accepts_project_id(self) -> None:
        req = UsagePerPeriodInput(start_date="20200601", end_date="20200630", project_id="proj-abc")
        assert req.project_id == "proj-abc"

    def test_accepts_project_id_via_group_id_alias(self) -> None:
        req = UsagePerPeriodInput.model_validate({
            "start_date": "20200601",
            "end_date": "20200630",
            "group_id": "g-001",
        })
        assert req.project_id == "g-001"

    def test_invalid_start_date_too_short_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            UsagePerPeriodInput(start_date="2020060", end_date="20200630")

    def test_invalid_start_date_too_long_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            UsagePerPeriodInput(start_date="202006010", end_date="20200630")

    def test_invalid_start_date_with_letters_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            UsagePerPeriodInput(start_date="2020AB01", end_date="20200630")

    def test_invalid_end_date_too_short_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            UsagePerPeriodInput(start_date="20200601", end_date="2020063")

    def test_invalid_end_date_with_dashes_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            UsagePerPeriodInput(start_date="20200601", end_date="2020-06-30")

    def test_missing_start_date_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            UsagePerPeriodInput.model_validate({"end_date": "20200630"})

    def test_missing_end_date_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            UsagePerPeriodInput.model_validate({"start_date": "20200601"})


class TestWatcherAgentInput:
    """Tests for WatcherAgentInput model."""

    def test_valid_creation_with_agent_id(self) -> None:
        req = WatcherAgentInput(agent_id="agent-01")
        assert req.agent_id == "agent-01"

    def test_accepts_agent_via_agent_alias(self) -> None:
        req = WatcherAgentInput.model_validate({"agent": "agent-02"})
        assert req.agent_id == "agent-02"

    def test_missing_agent_id_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            WatcherAgentInput.model_validate({})

    def test_agent_id_is_string(self) -> None:
        req = WatcherAgentInput(agent_id="my-agent")
        assert isinstance(req.agent_id, str)
