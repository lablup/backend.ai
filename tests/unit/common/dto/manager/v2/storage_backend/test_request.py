"""Unit tests for the storage backend v2 request DTOs."""

from __future__ import annotations

import uuid

import pytest
from pydantic import ValidationError

from ai.backend.common.dto.manager.query import StringFilter, UUIDFilter
from ai.backend.common.dto.manager.v2.storage_backend.request import (
    AdminSearchStorageBackendsInput,
    SearchServiceStorageBackendStatusesInput,
    ServiceStorageBackendStatusFilter,
    StorageBackendFilter,
    StorageBackendOrder,
    UpdateStorageBackendInput,
)
from ai.backend.common.dto.manager.v2.storage_backend.types import (
    OrderDirection,
    ServiceStorageBackendStatusOrderField,
    StorageBackendOrderField,
)
from ai.backend.common.exception import BackendAISchemaValidationFailed
from ai.backend.common.tristate.unset import UNSET


class TestUpdateStorageBackendInput:
    def test_omitted_name_stays_unset(self) -> None:
        assert UpdateStorageBackendInput().name is UNSET

    def test_name_is_taken_as_given(self) -> None:
        """``String64`` does not strip, so the surrounding space is kept."""
        assert UpdateStorageBackendInput(name="  vfs-1  ").name == "  vfs-1  "

    def test_empty_name_is_refused(self) -> None:
        with pytest.raises(ValidationError):
            UpdateStorageBackendInput(name="")

    def test_name_longer_than_the_column_is_refused(self) -> None:
        with pytest.raises(ValidationError):
            UpdateStorageBackendInput(name="x" * 65)

    def test_name_of_the_column_length_is_accepted(self) -> None:
        name = "x" * 64
        assert UpdateStorageBackendInput(name=name).name == name


class TestStorageBackendFilter:
    def test_every_field_defaults_to_none(self) -> None:
        filter = StorageBackendFilter()
        assert filter.entity_id is None
        assert filter.name is None
        assert filter.storage_backend_type_id is None
        assert filter.AND is None

    def test_nested_filters_hold_their_own_conditions(self) -> None:
        backend_id = uuid.uuid4()
        filter = StorageBackendFilter(
            name=StringFilter(contains="vfs"),
            AND=[StorageBackendFilter(entity_id=UUIDFilter(equals=backend_id))],
        )
        assert filter.AND is not None
        nested = filter.AND[0]
        assert nested.entity_id is not None
        assert nested.entity_id.equals == backend_id


class TestAdminSearchStorageBackendsInput:
    def test_pagination_defaults_are_empty(self) -> None:
        input = AdminSearchStorageBackendsInput()
        assert input.first is None
        assert input.limit is None
        assert input.offset is None

    def test_order_carries_the_field_and_the_direction(self) -> None:
        input = AdminSearchStorageBackendsInput(
            order=[
                StorageBackendOrder(
                    field=StorageBackendOrderField.NAME, direction=OrderDirection.DESC
                )
            ]
        )
        assert input.order is not None
        assert input.order[0].field is StorageBackendOrderField.NAME
        assert input.order[0].direction is OrderDirection.DESC

    def test_order_direction_defaults_to_ascending(self) -> None:
        order = StorageBackendOrder(field=StorageBackendOrderField.CREATED_AT)
        assert order.direction is OrderDirection.ASC

    @pytest.mark.parametrize(
        ("field", "value"),
        [("first", 0), ("last", 0), ("limit", 0), ("offset", -1)],
    )
    def test_out_of_range_pagination_is_refused(self, field: str, value: int) -> None:
        with pytest.raises((BackendAISchemaValidationFailed, ValidationError)):
            AdminSearchStorageBackendsInput.model_validate({field: value})


class TestSearchServiceStorageBackendStatusesInput:
    def test_filter_names_either_side_of_the_pair(self) -> None:
        service_id = uuid.uuid4()
        backend_id = uuid.uuid4()
        input = SearchServiceStorageBackendStatusesInput(
            filter=ServiceStorageBackendStatusFilter(
                service_catalog_id=UUIDFilter(equals=service_id),
                storage_backend_id=UUIDFilter(equals=backend_id),
            )
        )
        assert input.filter is not None
        assert input.filter.service_catalog_id is not None
        assert input.filter.service_catalog_id.equals == service_id
        assert input.filter.storage_backend_id is not None
        assert input.filter.storage_backend_id.equals == backend_id

    def test_order_fields_cover_the_pair_the_check_time_and_the_update_time(self) -> None:
        assert {f.value for f in ServiceStorageBackendStatusOrderField} == {
            "service_catalog_id",
            "storage_backend_id",
            "status_checked_at",
            "updated_at",
        }
