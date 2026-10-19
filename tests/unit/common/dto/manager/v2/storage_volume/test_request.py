"""Unit tests for the storage volume v2 request DTOs."""

from __future__ import annotations

import uuid

import pytest
from pydantic import ValidationError

from ai.backend.common.data.storage.types import StorageVolumeUsageField
from ai.backend.common.dto.manager.query import StringFilter, UUIDFilter
from ai.backend.common.dto.manager.v2.rbac.types import UUIDScope
from ai.backend.common.dto.manager.v2.storage_volume.request import (
    AdminSearchStorageVolumesInput,
    ScopedSearchStorageVolumesInput,
    StorageVolumeFilter,
    StorageVolumeOrder,
    StorageVolumeScope,
    UpdateStorageVolumeInput,
)
from ai.backend.common.dto.manager.v2.storage_volume.types import (
    OrderDirection,
    StorageVolumeOrderField,
    StorageVolumeUsageExposureInput,
)
from ai.backend.common.exception import BackendAISchemaValidationFailed
from ai.backend.common.tristate.unset import UNSET


def _a_scope() -> StorageVolumeScope:
    return StorageVolumeScope(domain=[UUIDScope(value=uuid.uuid4())])


class TestUpdateStorageVolumeInput:
    def test_every_field_stays_unset_when_omitted(self) -> None:
        input = UpdateStorageVolumeInput()
        assert input.name is UNSET
        assert input.status_stale_after_seconds is UNSET
        assert input.usage_exposure is UNSET

    def test_name_is_taken_as_given(self) -> None:
        """``String64`` does not strip, so the surrounding space is kept."""
        assert UpdateStorageVolumeInput(name="  local  ").name == "  local  "

    def test_empty_name_is_refused(self) -> None:
        with pytest.raises(ValidationError):
            UpdateStorageVolumeInput(name="")

    def test_name_longer_than_the_column_is_refused(self) -> None:
        with pytest.raises(ValidationError):
            UpdateStorageVolumeInput(name="x" * 65)

    def test_stale_threshold_is_kept_in_seconds(self) -> None:
        assert (
            UpdateStorageVolumeInput(status_stale_after_seconds=3600).status_stale_after_seconds
            == 3600
        )

    @pytest.mark.parametrize("seconds", [0, -1])
    def test_non_positive_stale_threshold_is_refused(self, seconds: int) -> None:
        with pytest.raises(ValidationError):
            UpdateStorageVolumeInput(status_stale_after_seconds=seconds)

    def test_usage_exposure_replaces_the_whole_set(self) -> None:
        input = UpdateStorageVolumeInput(
            usage_exposure=StorageVolumeUsageExposureInput(
                exposed=[
                    StorageVolumeUsageField.USED_BYTES,
                    StorageVolumeUsageField.CAPACITY_BYTES,
                ]
            )
        )
        assert isinstance(input.usage_exposure, StorageVolumeUsageExposureInput)
        assert input.usage_exposure.exposed == [
            StorageVolumeUsageField.USED_BYTES,
            StorageVolumeUsageField.CAPACITY_BYTES,
        ]


class TestStorageVolumeFilter:
    def test_every_field_defaults_to_none(self) -> None:
        filter = StorageVolumeFilter()
        assert filter.entity_id is None
        assert filter.name is None
        assert filter.storage_backend_id is None

    def test_nested_filters_hold_their_own_conditions(self) -> None:
        volume_id = uuid.uuid4()
        filter = StorageVolumeFilter(
            name=StringFilter(contains="local"),
            OR=[StorageVolumeFilter(entity_id=UUIDFilter(equals=volume_id))],
        )
        assert filter.OR is not None
        nested = filter.OR[0]
        assert nested.entity_id is not None
        assert nested.entity_id.equals == volume_id


class TestStorageVolumeScope:
    def test_an_empty_scope_is_refused(self) -> None:
        with pytest.raises((BackendAISchemaValidationFailed, ValidationError)):
            StorageVolumeScope()

    @pytest.mark.parametrize("field", ["domain", "project", "user", "storage_backend"])
    def test_one_dimension_is_enough(self, field: str) -> None:
        scope = StorageVolumeScope.model_validate({field: [{"value": str(uuid.uuid4())}]})
        assert getattr(scope, field) is not None

    def test_the_other_dimensions_stay_none(self) -> None:
        scope = _a_scope()
        assert scope.project is None
        assert scope.user is None
        assert scope.storage_backend is None


class TestAdminSearchStorageVolumesInput:
    def test_it_takes_no_scope(self) -> None:
        """The administrator's search reads the whole system, so it names no scope."""
        assert "scope" not in AdminSearchStorageVolumesInput.model_fields

    def test_order_carries_the_field_and_the_direction(self) -> None:
        input = AdminSearchStorageVolumesInput(
            order=[
                StorageVolumeOrder(
                    field=StorageVolumeOrderField.NAME, direction=OrderDirection.DESC
                )
            ],
        )
        assert input.order is not None
        assert input.order[0].field is StorageVolumeOrderField.NAME
        assert input.order[0].direction is OrderDirection.DESC

    @pytest.mark.parametrize(
        ("field", "value"),
        [("first", 0), ("last", 0), ("limit", 0), ("offset", -1)],
    )
    def test_out_of_range_pagination_is_refused(self, field: str, value: int) -> None:
        with pytest.raises((BackendAISchemaValidationFailed, ValidationError)):
            AdminSearchStorageVolumesInput.model_validate({field: value})


class TestScopedSearchStorageVolumesInput:
    def test_the_scope_is_required(self) -> None:
        with pytest.raises((BackendAISchemaValidationFailed, ValidationError)):
            ScopedSearchStorageVolumesInput.model_validate({})

    def test_the_scope_is_carried(self) -> None:
        backend_id = uuid.uuid4()
        input = ScopedSearchStorageVolumesInput(
            scope=StorageVolumeScope(storage_backend=[UUIDScope(value=backend_id)])
        )
        assert input.scope.storage_backend is not None
        assert input.scope.storage_backend[0].value == backend_id
