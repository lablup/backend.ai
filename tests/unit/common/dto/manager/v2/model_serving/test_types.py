"""Tests for ai.backend.common.dto.manager.v2.model_serving.types module."""

from __future__ import annotations

import json
import uuid

from ai.backend.common.data.endpoint.types import EndpointLifecycle
from ai.backend.common.dto.manager.v2.model_serving.types import (
    EndpointLifecycle as ExportedEndpointLifecycle,
)
from ai.backend.common.dto.manager.v2.model_serving.types import (
    OrderDirection,
    RouteInfoSummary,
    ServiceOrderField,
)
from ai.backend.common.dto.manager.v2.model_serving.types import (
    RuntimeVariant as ExportedRuntimeVariant,
)
from ai.backend.common.types import RuntimeVariant


class TestOrderDirection:
    """Tests for OrderDirection enum."""

    def test_asc_value(self) -> None:
        assert OrderDirection.ASC.value == "asc"

    def test_desc_value(self) -> None:
        assert OrderDirection.DESC.value == "desc"

    def test_all_values_are_strings(self) -> None:
        for member in OrderDirection:
            assert isinstance(member.value, str)

    def test_enum_members_count(self) -> None:
        members = list(OrderDirection)
        assert len(members) == 2

    def test_from_string_asc(self) -> None:
        assert OrderDirection("asc") is OrderDirection.ASC

    def test_from_string_desc(self) -> None:
        assert OrderDirection("desc") is OrderDirection.DESC


class TestServiceOrderField:
    """Tests for ServiceOrderField enum."""

    def test_name_value(self) -> None:
        assert ServiceOrderField.NAME.value == "name"

    def test_created_at_value(self) -> None:
        assert ServiceOrderField.CREATED_AT.value == "created_at"

    def test_all_values_are_strings(self) -> None:
        for member in ServiceOrderField:
            assert isinstance(member.value, str)

    def test_enum_members_count(self) -> None:
        members = list(ServiceOrderField)
        assert len(members) == 2

    def test_from_string_name(self) -> None:
        assert ServiceOrderField("name") is ServiceOrderField.NAME

    def test_from_string_created_at(self) -> None:
        assert ServiceOrderField("created_at") is ServiceOrderField.CREATED_AT


class TestReExportedEnums:
    """Tests verifying that enums are properly re-exported from types module."""

    def test_endpoint_lifecycle_is_same_object(self) -> None:
        assert ExportedEndpointLifecycle is EndpointLifecycle

    def test_runtime_variant_is_same_object(self) -> None:
        assert ExportedRuntimeVariant is RuntimeVariant

    def test_endpoint_lifecycle_pending_value(self) -> None:
        assert ExportedEndpointLifecycle.PENDING.value == "pending"

    def test_endpoint_lifecycle_ready_value(self) -> None:
        assert ExportedEndpointLifecycle.READY.value == "ready"

    def test_runtime_variant_custom_value(self) -> None:
        assert ExportedRuntimeVariant.CUSTOM.value == "custom"

    def test_runtime_variant_vllm_value(self) -> None:
        assert ExportedRuntimeVariant.VLLM.value == "vllm"


class TestRouteInfoSummary:
    """Tests for RouteInfoSummary model creation and serialization."""

    def test_creation_with_session_id(self) -> None:
        route_id = uuid.uuid4()
        session_id = uuid.uuid4()
        summary = RouteInfoSummary(
            route_id=route_id,
            session_id=session_id,
            traffic_ratio=0.5,
        )
        assert summary.route_id == route_id
        assert summary.session_id == session_id
        assert summary.traffic_ratio == 0.5

    def test_creation_without_session_id(self) -> None:
        route_id = uuid.uuid4()
        summary = RouteInfoSummary(
            route_id=route_id,
            session_id=None,
            traffic_ratio=1.0,
        )
        assert summary.route_id == route_id
        assert summary.session_id is None
        assert summary.traffic_ratio == 1.0

    def test_model_dump_json(self) -> None:
        route_id = uuid.uuid4()
        session_id = uuid.uuid4()
        summary = RouteInfoSummary(
            route_id=route_id,
            session_id=session_id,
            traffic_ratio=0.5,
        )
        data = json.loads(summary.model_dump_json())
        assert data["traffic_ratio"] == 0.5
        assert data["session_id"] is not None

    def test_null_session_id_serialized_as_null(self) -> None:
        summary = RouteInfoSummary(
            route_id=uuid.uuid4(),
            session_id=None,
            traffic_ratio=1.0,
        )
        data = json.loads(summary.model_dump_json())
        assert data["session_id"] is None

    def test_serialization_round_trip(self) -> None:
        route_id = uuid.uuid4()
        session_id = uuid.uuid4()
        summary = RouteInfoSummary(
            route_id=route_id,
            session_id=session_id,
            traffic_ratio=0.75,
        )
        json_str = summary.model_dump_json()
        restored = RouteInfoSummary.model_validate_json(json_str)
        assert restored.route_id == route_id
        assert restored.session_id == session_id
        assert restored.traffic_ratio == 0.75

    def test_serialization_round_trip_no_session(self) -> None:
        route_id = uuid.uuid4()
        summary = RouteInfoSummary(
            route_id=route_id,
            session_id=None,
            traffic_ratio=1.0,
        )
        json_str = summary.model_dump_json()
        restored = RouteInfoSummary.model_validate_json(json_str)
        assert restored.route_id == route_id
        assert restored.session_id is None
        assert restored.traffic_ratio == 1.0
