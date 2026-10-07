"""Tests for ai.backend.common.dto.manager.v2.service_catalog.types module."""

from __future__ import annotations

from ai.backend.common.dto.manager.v2.service_catalog.types import (
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
        assert OrderDirection.ASC.value == "ASC"

    def test_desc_value(self) -> None:
        assert OrderDirection.DESC.value == "DESC"

    def test_all_values_are_strings(self) -> None:
        for member in OrderDirection:
            assert isinstance(member.value, str)

    def test_enum_members_count(self) -> None:
        members = list(OrderDirection)
        assert len(members) == 2

    def test_from_string_asc(self) -> None:
        assert OrderDirection("ASC") is OrderDirection.ASC

    def test_from_string_desc(self) -> None:
        assert OrderDirection("DESC") is OrderDirection.DESC


class TestServiceCatalogOrderField:
    """Tests for ServiceCatalogOrderField enum."""

    def test_service_group_value(self) -> None:
        assert ServiceCatalogOrderField.SERVICE_GROUP.value == "service_group"

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
        assert len(members) == 5

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
