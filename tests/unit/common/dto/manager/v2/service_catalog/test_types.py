"""Tests for ai.backend.common.dto.manager.v2.service_catalog.types module."""

from __future__ import annotations

import json
import uuid

from ai.backend.common.dto.manager.v2.service_catalog.types import (
    EndpointInfo,
    OrderDirection,
    ServiceCatalogOrderField,
)
from ai.backend.common.dto.manager.v2.service_catalog.types import (
    ServiceCatalogStatus as ExportedServiceCatalogStatus,
)
from ai.backend.common.types import ServiceCatalogStatus


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


class TestServiceCatalogOrderField:
    """Tests for ServiceCatalogOrderField enum."""

    def test_display_name_value(self) -> None:
        assert ServiceCatalogOrderField.DISPLAY_NAME.value == "display_name"

    def test_registered_at_value(self) -> None:
        assert ServiceCatalogOrderField.REGISTERED_AT.value == "registered_at"

    def test_last_heartbeat_value(self) -> None:
        assert ServiceCatalogOrderField.LAST_HEARTBEAT.value == "last_heartbeat"

    def test_status_value(self) -> None:
        assert ServiceCatalogOrderField.STATUS.value == "status"

    def test_all_values_are_strings(self) -> None:
        for member in ServiceCatalogOrderField:
            assert isinstance(member.value, str)

    def test_enum_members_count(self) -> None:
        members = list(ServiceCatalogOrderField)
        assert len(members) == 4

    def test_from_string_display_name(self) -> None:
        assert ServiceCatalogOrderField("display_name") is ServiceCatalogOrderField.DISPLAY_NAME

    def test_from_string_registered_at(self) -> None:
        assert ServiceCatalogOrderField("registered_at") is ServiceCatalogOrderField.REGISTERED_AT


class TestReExportedEnums:
    """Tests verifying that enums are properly re-exported from types module."""

    def test_service_catalog_status_is_same_object(self) -> None:
        assert ExportedServiceCatalogStatus is ServiceCatalogStatus

    def test_service_catalog_status_healthy_value(self) -> None:
        assert ExportedServiceCatalogStatus.HEALTHY.value == "healthy"

    def test_service_catalog_status_unhealthy_value(self) -> None:
        assert ExportedServiceCatalogStatus.UNHEALTHY.value == "unhealthy"

    def test_service_catalog_status_deregistered_value(self) -> None:
        assert ExportedServiceCatalogStatus.DEREGISTERED.value == "deregistered"


class TestEndpointInfo:
    """Tests for EndpointInfo model creation and serialization."""

    def test_creation_with_all_fields(self) -> None:
        endpoint_id = uuid.uuid4()
        info = EndpointInfo(
            id=endpoint_id,
            role="primary",
            scope="internal",
            address="192.168.1.100",
            port=8080,
            protocol="http",
            metadata={"region": "us-east"},
        )
        assert info.id == endpoint_id
        assert info.role == "primary"
        assert info.scope == "internal"
        assert info.address == "192.168.1.100"
        assert info.port == 8080
        assert info.protocol == "http"
        assert info.metadata == {"region": "us-east"}

    def test_creation_without_metadata(self) -> None:
        info = EndpointInfo(
            id=uuid.uuid4(),
            role="secondary",
            scope="external",
            address="10.0.0.1",
            port=443,
            protocol="https",
            metadata=None,
        )
        assert info.metadata is None

    def test_model_dump_json(self) -> None:
        endpoint_id = uuid.uuid4()
        info = EndpointInfo(
            id=endpoint_id,
            role="primary",
            scope="internal",
            address="127.0.0.1",
            port=9000,
            protocol="grpc",
            metadata=None,
        )
        data = json.loads(info.model_dump_json())
        assert data["role"] == "primary"
        assert data["port"] == 9000
        assert data["metadata"] is None

    def test_serialization_round_trip(self) -> None:
        endpoint_id = uuid.uuid4()
        info = EndpointInfo(
            id=endpoint_id,
            role="primary",
            scope="internal",
            address="192.168.1.100",
            port=8080,
            protocol="http",
            metadata={"key": "value"},
        )
        json_str = info.model_dump_json()
        restored = EndpointInfo.model_validate_json(json_str)
        assert restored.id == endpoint_id
        assert restored.role == "primary"
        assert restored.scope == "internal"
        assert restored.address == "192.168.1.100"
        assert restored.port == 8080
        assert restored.protocol == "http"
        assert restored.metadata == {"key": "value"}

    def test_serialization_round_trip_no_metadata(self) -> None:
        endpoint_id = uuid.uuid4()
        info = EndpointInfo(
            id=endpoint_id,
            role="secondary",
            scope="external",
            address="10.0.0.2",
            port=443,
            protocol="https",
            metadata=None,
        )
        json_str = info.model_dump_json()
        restored = EndpointInfo.model_validate_json(json_str)
        assert restored.id == endpoint_id
        assert restored.metadata is None
