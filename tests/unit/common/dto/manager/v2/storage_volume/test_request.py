"""Unit tests for the storage volume v2 request DTOs."""

from __future__ import annotations

import uuid

import pytest
from pydantic import ValidationError

from ai.backend.common.data.storage.types import StorageVolumeUsageField
from ai.backend.common.dto.manager.query import StringFilter, UUIDFilter
from ai.backend.common.dto.manager.v2.storage_volume.request import (
    AdminSearchStorageVolumesInput,
    PurgeResourceGroupVolumeOfferInput,
    ResourceGroupVolumeOfferFilter,
    SearchResourceGroupVolumeOffersInput,
    SearchStorageVolumeServiceHoldingsInput,
    StorageVolumeFilter,
    StorageVolumeOrder,
    StorageVolumeServiceHoldingFilter,
    UpdateStorageVolumeInput,
    UpsertResourceGroupVolumeOfferInput,
)
from ai.backend.common.dto.manager.v2.storage_volume.types import (
    OrderDirection,
    ResourceGroupVolumeOfferOrderField,
    StorageVolumeOrderField,
    StorageVolumeServiceHoldingOrderField,
    StorageVolumeUsageExposureInput,
)
from ai.backend.common.tristate.unset import UNSET


class TestUpdateStorageVolumeInput:
    def test_every_field_stays_unset_when_omitted(self) -> None:
        input = UpdateStorageVolumeInput()
        assert input.name is UNSET
        assert input.status_stale_after_seconds is UNSET
        assert input.usage_exposure is UNSET

    def test_name_is_stripped(self) -> None:
        assert UpdateStorageVolumeInput(name="  local  ").name == "local"

    def test_blank_name_is_refused(self) -> None:
        with pytest.raises(ValidationError):
            UpdateStorageVolumeInput(name=" ")

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


class TestAdminSearchStorageVolumesInput:
    def test_order_carries_the_field_and_the_direction(self) -> None:
        input = AdminSearchStorageVolumesInput(
            order=[
                StorageVolumeOrder(
                    field=StorageVolumeOrderField.NAME, direction=OrderDirection.DESC
                )
            ]
        )
        assert input.order is not None
        assert input.order[0].field is StorageVolumeOrderField.NAME
        assert input.order[0].direction is OrderDirection.DESC

    @pytest.mark.parametrize(
        ("field", "value"),
        [("first", 0), ("last", 0), ("limit", 0), ("offset", -1)],
    )
    def test_out_of_range_pagination_is_refused(self, field: str, value: int) -> None:
        with pytest.raises(ValidationError):
            AdminSearchStorageVolumesInput.model_validate({field: value})


class TestSearchStorageVolumeServiceHoldingsInput:
    def test_filter_names_either_side_of_the_pair(self) -> None:
        service_id = uuid.uuid4()
        volume_id = uuid.uuid4()
        input = SearchStorageVolumeServiceHoldingsInput(
            filter=StorageVolumeServiceHoldingFilter(
                service_catalog_id=UUIDFilter(equals=service_id),
                storage_volume_id=UUIDFilter(equals=volume_id),
            )
        )
        assert input.filter is not None
        assert input.filter.service_catalog_id is not None
        assert input.filter.service_catalog_id.equals == service_id
        assert input.filter.storage_volume_id is not None
        assert input.filter.storage_volume_id.equals == volume_id


class TestSearchResourceGroupVolumeOffersInput:
    def test_offer_flags_are_plain_booleans(self) -> None:
        input = SearchResourceGroupVolumeOffersInput(
            filter=ResourceGroupVolumeOfferFilter(enabled=True, is_default=False)
        )
        assert input.filter is not None
        assert input.filter.enabled is True
        assert input.filter.is_default is False

    def test_offer_flags_default_to_none(self) -> None:
        filter = ResourceGroupVolumeOfferFilter()
        assert filter.enabled is None
        assert filter.is_default is None

    def test_nested_filters_hold_their_own_conditions(self) -> None:
        resource_group_id = uuid.uuid4()
        filter = ResourceGroupVolumeOfferFilter(
            NOT=[
                ResourceGroupVolumeOfferFilter(
                    resource_group_id=UUIDFilter(equals=resource_group_id)
                )
            ]
        )
        assert filter.NOT is not None
        nested = filter.NOT[0]
        assert nested.resource_group_id is not None
        assert nested.resource_group_id.equals == resource_group_id


class TestUpsertResourceGroupVolumeOfferInput:
    def test_the_pair_is_required(self) -> None:
        with pytest.raises(ValidationError):
            UpsertResourceGroupVolumeOfferInput.model_validate({
                "resource_group_id": str(uuid.uuid4())
            })

    def test_flags_stay_unset_when_omitted(self) -> None:
        input = UpsertResourceGroupVolumeOfferInput(
            resource_group_id=uuid.uuid4(), storage_volume_id=uuid.uuid4()
        )
        assert input.enabled is UNSET
        assert input.is_default is UNSET

    def test_flags_are_carried(self) -> None:
        input = UpsertResourceGroupVolumeOfferInput(
            resource_group_id=uuid.uuid4(),
            storage_volume_id=uuid.uuid4(),
            enabled=False,
            is_default=True,
        )
        assert input.enabled is False
        assert input.is_default is True


class TestPurgeResourceGroupVolumeOfferInput:
    def test_the_pair_is_required(self) -> None:
        with pytest.raises(ValidationError):
            PurgeResourceGroupVolumeOfferInput.model_validate({
                "storage_volume_id": str(uuid.uuid4())
            })

    def test_the_pair_is_carried(self) -> None:
        resource_group_id, storage_volume_id = uuid.uuid4(), uuid.uuid4()
        input = PurgeResourceGroupVolumeOfferInput(
            resource_group_id=resource_group_id, storage_volume_id=storage_volume_id
        )
        assert input.resource_group_id == resource_group_id
        assert input.storage_volume_id == storage_volume_id


class TestChildRowOrderFields:
    def test_holdings_order_by_the_pair_the_check_time_or_the_update_time(self) -> None:
        assert {f.value for f in StorageVolumeServiceHoldingOrderField} == {
            "service_catalog_id",
            "storage_volume_id",
            "status_checked_at",
            "updated_at",
        }

    def test_offers_order_by_the_pair_the_default_flag_or_the_update_time(self) -> None:
        assert {f.value for f in ResourceGroupVolumeOfferOrderField} == {
            "resource_group_id",
            "storage_volume_id",
            "is_default",
            "updated_at",
        }
