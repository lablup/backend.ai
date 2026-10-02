"""Tests for converting a service catalog row, with its ``endpoint_rows``, into data."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

import pytest

from ai.backend.common.data.entity.service_catalog import (
    ServiceCatalogEndpointID,
    ServiceCatalogID,
)
from ai.backend.common.exception import BackendAISchemaValidationFailed
from ai.backend.common.types import ServiceCatalogStatus
from ai.backend.manager.models.service_catalog.row import ServiceCatalogRow
from ai.backend.manager.models.service_catalog.searchable_fields import (
    ServiceCatalogSearchableFields,
)


def _endpoint_json(service_id: uuid.UUID, role: str, **overrides: Any) -> dict[str, Any]:
    endpoint: dict[str, Any] = {
        "id": str(uuid.uuid4()),
        "service_id": str(service_id),
        "role": role,
        "scope": "public",
        "address": "10.0.0.1",
        "port": 8080,
        "protocol": "http",
        "metadata": {"weight": 1},
    }
    endpoint.update(overrides)
    return endpoint


class TestServiceCatalogToData:
    @pytest.fixture
    def service_row(self) -> ServiceCatalogRow:
        now = datetime.now(UTC)
        return ServiceCatalogRow(
            id=ServiceCatalogID(uuid.uuid4()),
            service_group="manager",
            instance_id="manager-1",
            display_name="Manager 1",
            version="26.10.0",
            labels={},
            status=ServiceCatalogStatus.HEALTHY,
            startup_time=now,
            registered_at=now,
            last_heartbeat=now,
            config_hash="",
        )

    @pytest.fixture
    def service_with_two_endpoints(
        self, service_row: ServiceCatalogRow
    ) -> tuple[ServiceCatalogRow, list[dict[str, Any]]]:
        endpoints = [
            _endpoint_json(service_row.id, "main"),
            _endpoint_json(service_row.id, "health", port=8081),
        ]
        service_row.endpoint_rows = endpoints
        return service_row, endpoints

    @pytest.fixture
    def service_with_null_metadata_endpoint(
        self, service_row: ServiceCatalogRow
    ) -> ServiceCatalogRow:
        service_row.endpoint_rows = [_endpoint_json(service_row.id, "main", metadata=None)]
        return service_row

    @pytest.fixture
    def service_with_portless_endpoint(self, service_row: ServiceCatalogRow) -> ServiceCatalogRow:
        endpoint = _endpoint_json(service_row.id, "main")
        del endpoint["port"]
        service_row.endpoint_rows = [endpoint]
        return service_row

    def test_endpoint_rows_become_endpoints_with_their_own_id_types(
        self, service_with_two_endpoints: tuple[ServiceCatalogRow, list[dict[str, Any]]]
    ) -> None:
        row, endpoints = service_with_two_endpoints

        data = ServiceCatalogSearchableFields.own.to_data(row)

        assert [endpoint.role for endpoint in data.endpoints] == ["main", "health"]
        assert [endpoint.port for endpoint in data.endpoints] == [8080, 8081]
        for endpoint, raw in zip(data.endpoints, endpoints, strict=True):
            assert isinstance(endpoint.id, ServiceCatalogEndpointID)
            assert endpoint.id == uuid.UUID(raw["id"])
            assert isinstance(endpoint.service_id, ServiceCatalogID)
            assert endpoint.service_id == row.id

    def test_endpoint_rows_not_loaded_become_no_endpoints(
        self, service_row: ServiceCatalogRow
    ) -> None:
        data = ServiceCatalogSearchableFields.own.to_data(service_row)

        assert data.endpoints == []

    def test_endpoint_with_null_metadata_keeps_it_none(
        self, service_with_null_metadata_endpoint: ServiceCatalogRow
    ) -> None:
        data = ServiceCatalogSearchableFields.own.to_data(service_with_null_metadata_endpoint)

        assert data.endpoints[0].metadata is None

    def test_endpoint_missing_a_required_field_is_refused(
        self, service_with_portless_endpoint: ServiceCatalogRow
    ) -> None:
        with pytest.raises(BackendAISchemaValidationFailed):
            ServiceCatalogSearchableFields.own.to_data(service_with_portless_endpoint)
