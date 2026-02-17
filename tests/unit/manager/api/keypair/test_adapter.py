"""
Tests for keypair API adapter classes.
Tests conversion from DTO objects to repository Querier objects.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import cast

from ai.backend.common.dto.manager.keypair import (
    KeyPairDTO,
    KeyPairFilter,
    KeyPairOrder,
    KeyPairOrderField,
    OrderDirection,
    SearchKeyPairsRequest,
    StringFilter,
    UpdateKeyPairRequest,
)
from ai.backend.common.types import AccessKey, SecretKey
from ai.backend.manager.api.keypair.adapter import (
    KeyPairAdapter,
    KeyPairUpdaterSpec,
)
from ai.backend.manager.data.keypair.types import KeyPairData
from ai.backend.manager.repositories.base import OffsetPagination


class TestKeyPairAdapterQuerier:
    """Test cases for KeyPairAdapter.build_querier"""

    def test_empty_querier(self) -> None:
        """Test building querier with no filters, orders, and default limit"""
        request = SearchKeyPairsRequest()
        adapter = KeyPairAdapter()
        querier = adapter.build_querier(request)

        assert len(querier.conditions) == 0
        assert len(querier.orders) == 0
        assert querier.pagination is not None
        assert isinstance(querier.pagination, OffsetPagination)
        assert querier.pagination.limit == 50
        assert querier.pagination.offset == 0

    def test_user_id_equals_case_sensitive(self) -> None:
        """Test user_id equals filter (case-sensitive)"""
        request = SearchKeyPairsRequest(
            filter=KeyPairFilter(
                user_id=StringFilter(equals="user@example.com"),
            )
        )
        adapter = KeyPairAdapter()
        querier = adapter.build_querier(request)

        assert len(querier.conditions) == 1
        condition_result = querier.conditions[0]()
        assert condition_result is not None

    def test_user_id_equals_case_insensitive(self) -> None:
        """Test user_id equals filter (case-insensitive)"""
        request = SearchKeyPairsRequest(
            filter=KeyPairFilter(
                user_id=StringFilter(i_equals="user@example.com"),
            )
        )
        adapter = KeyPairAdapter()
        querier = adapter.build_querier(request)

        assert len(querier.conditions) == 1
        condition_result = querier.conditions[0]()
        assert condition_result is not None

    def test_user_id_contains_case_sensitive(self) -> None:
        """Test user_id contains filter (case-sensitive)"""
        request = SearchKeyPairsRequest(
            filter=KeyPairFilter(
                user_id=StringFilter(contains="example"),
            )
        )
        adapter = KeyPairAdapter()
        querier = adapter.build_querier(request)

        assert len(querier.conditions) == 1
        condition_result = querier.conditions[0]()
        assert condition_result is not None

    def test_user_id_contains_case_insensitive(self) -> None:
        """Test user_id contains filter (case-insensitive)"""
        request = SearchKeyPairsRequest(
            filter=KeyPairFilter(
                user_id=StringFilter(i_contains="example"),
            )
        )
        adapter = KeyPairAdapter()
        querier = adapter.build_querier(request)

        assert len(querier.conditions) == 1
        condition_result = querier.conditions[0]()
        assert condition_result is not None

    def test_user_id_starts_with(self) -> None:
        """Test user_id starts_with filter"""
        request = SearchKeyPairsRequest(
            filter=KeyPairFilter(
                user_id=StringFilter(starts_with="user"),
            )
        )
        adapter = KeyPairAdapter()
        querier = adapter.build_querier(request)

        assert len(querier.conditions) == 1
        condition_result = querier.conditions[0]()
        assert condition_result is not None

    def test_user_id_ends_with(self) -> None:
        """Test user_id ends_with filter"""
        request = SearchKeyPairsRequest(
            filter=KeyPairFilter(
                user_id=StringFilter(ends_with=".com"),
            )
        )
        adapter = KeyPairAdapter()
        querier = adapter.build_querier(request)

        assert len(querier.conditions) == 1
        condition_result = querier.conditions[0]()
        assert condition_result is not None

    def test_access_key_equals_case_sensitive(self) -> None:
        """Test access_key equals filter (case-sensitive)"""
        request = SearchKeyPairsRequest(
            filter=KeyPairFilter(
                access_key=StringFilter(equals="AKIAIOSFODNN7EXAMPLE"),
            )
        )
        adapter = KeyPairAdapter()
        querier = adapter.build_querier(request)

        assert len(querier.conditions) == 1
        condition_result = querier.conditions[0]()
        assert condition_result is not None

    def test_access_key_contains_case_insensitive(self) -> None:
        """Test access_key contains filter (case-insensitive)"""
        request = SearchKeyPairsRequest(
            filter=KeyPairFilter(
                access_key=StringFilter(i_contains="akia"),
            )
        )
        adapter = KeyPairAdapter()
        querier = adapter.build_querier(request)

        assert len(querier.conditions) == 1
        condition_result = querier.conditions[0]()
        assert condition_result is not None

    def test_access_key_starts_with(self) -> None:
        """Test access_key starts_with filter"""
        request = SearchKeyPairsRequest(
            filter=KeyPairFilter(
                access_key=StringFilter(starts_with="AKIA"),
            )
        )
        adapter = KeyPairAdapter()
        querier = adapter.build_querier(request)

        assert len(querier.conditions) == 1
        condition_result = querier.conditions[0]()
        assert condition_result is not None

    def test_access_key_ends_with(self) -> None:
        """Test access_key ends_with filter"""
        request = SearchKeyPairsRequest(
            filter=KeyPairFilter(
                access_key=StringFilter(ends_with="EXAMPLE"),
            )
        )
        adapter = KeyPairAdapter()
        querier = adapter.build_querier(request)

        assert len(querier.conditions) == 1
        condition_result = querier.conditions[0]()
        assert condition_result is not None

    def test_is_active_filter_true(self) -> None:
        """Test is_active filter (True)"""
        request = SearchKeyPairsRequest(filter=KeyPairFilter(is_active=True))
        adapter = KeyPairAdapter()
        querier = adapter.build_querier(request)

        assert len(querier.conditions) == 1
        condition_result = querier.conditions[0]()
        assert condition_result is not None

    def test_is_active_filter_false(self) -> None:
        """Test is_active filter (False)"""
        request = SearchKeyPairsRequest(filter=KeyPairFilter(is_active=False))
        adapter = KeyPairAdapter()
        querier = adapter.build_querier(request)

        assert len(querier.conditions) == 1
        condition_result = querier.conditions[0]()
        assert condition_result is not None

    def test_is_admin_filter_true(self) -> None:
        """Test is_admin filter (True)"""
        request = SearchKeyPairsRequest(filter=KeyPairFilter(is_admin=True))
        adapter = KeyPairAdapter()
        querier = adapter.build_querier(request)

        assert len(querier.conditions) == 1
        condition_result = querier.conditions[0]()
        assert condition_result is not None

    def test_is_admin_filter_false(self) -> None:
        """Test is_admin filter (False)"""
        request = SearchKeyPairsRequest(filter=KeyPairFilter(is_admin=False))
        adapter = KeyPairAdapter()
        querier = adapter.build_querier(request)

        assert len(querier.conditions) == 1
        condition_result = querier.conditions[0]()
        assert condition_result is not None

    def test_resource_policy_equals_case_sensitive(self) -> None:
        """Test resource_policy equals filter (case-sensitive)"""
        request = SearchKeyPairsRequest(
            filter=KeyPairFilter(
                resource_policy=StringFilter(equals="default"),
            )
        )
        adapter = KeyPairAdapter()
        querier = adapter.build_querier(request)

        assert len(querier.conditions) == 1
        condition_result = querier.conditions[0]()
        assert condition_result is not None

    def test_resource_policy_contains_case_insensitive(self) -> None:
        """Test resource_policy contains filter (case-insensitive)"""
        request = SearchKeyPairsRequest(
            filter=KeyPairFilter(
                resource_policy=StringFilter(i_contains="default"),
            )
        )
        adapter = KeyPairAdapter()
        querier = adapter.build_querier(request)

        assert len(querier.conditions) == 1
        condition_result = querier.conditions[0]()
        assert condition_result is not None

    def test_resource_policy_starts_with(self) -> None:
        """Test resource_policy starts_with filter"""
        request = SearchKeyPairsRequest(
            filter=KeyPairFilter(
                resource_policy=StringFilter(starts_with="custom"),
            )
        )
        adapter = KeyPairAdapter()
        querier = adapter.build_querier(request)

        assert len(querier.conditions) == 1
        condition_result = querier.conditions[0]()
        assert condition_result is not None

    def test_resource_policy_ends_with(self) -> None:
        """Test resource_policy ends_with filter"""
        request = SearchKeyPairsRequest(
            filter=KeyPairFilter(
                resource_policy=StringFilter(ends_with="policy"),
            )
        )
        adapter = KeyPairAdapter()
        querier = adapter.build_querier(request)

        assert len(querier.conditions) == 1
        condition_result = querier.conditions[0]()
        assert condition_result is not None

    def test_multiple_filters_combined(self) -> None:
        """Test multiple filters combined"""
        request = SearchKeyPairsRequest(
            filter=KeyPairFilter(
                user_id=StringFilter(contains="user"),
                is_active=True,
                is_admin=False,
                resource_policy=StringFilter(equals="default"),
            )
        )
        adapter = KeyPairAdapter()
        querier = adapter.build_querier(request)

        assert len(querier.conditions) == 4
        for condition in querier.conditions:
            assert condition() is not None

    def test_order_by_access_key_ascending(self) -> None:
        """Test ordering by access_key ascending"""
        request = SearchKeyPairsRequest(
            order=[
                KeyPairOrder(
                    field=KeyPairOrderField.ACCESS_KEY,
                    direction=OrderDirection.ASC,
                )
            ]
        )
        adapter = KeyPairAdapter()
        querier = adapter.build_querier(request)

        assert len(querier.orders) == 1
        assert querier.orders[0] is not None

    def test_order_by_access_key_descending(self) -> None:
        """Test ordering by access_key descending"""
        request = SearchKeyPairsRequest(
            order=[
                KeyPairOrder(
                    field=KeyPairOrderField.ACCESS_KEY,
                    direction=OrderDirection.DESC,
                )
            ]
        )
        adapter = KeyPairAdapter()
        querier = adapter.build_querier(request)

        assert len(querier.orders) == 1
        assert querier.orders[0] is not None

    def test_order_by_created_at_ascending(self) -> None:
        """Test ordering by created_at ascending"""
        request = SearchKeyPairsRequest(
            order=[
                KeyPairOrder(
                    field=KeyPairOrderField.CREATED_AT,
                    direction=OrderDirection.ASC,
                )
            ]
        )
        adapter = KeyPairAdapter()
        querier = adapter.build_querier(request)

        assert len(querier.orders) == 1
        assert querier.orders[0] is not None

    def test_order_by_created_at_descending(self) -> None:
        """Test ordering by created_at descending"""
        request = SearchKeyPairsRequest(
            order=[
                KeyPairOrder(
                    field=KeyPairOrderField.CREATED_AT,
                    direction=OrderDirection.DESC,
                )
            ]
        )
        adapter = KeyPairAdapter()
        querier = adapter.build_querier(request)

        assert len(querier.orders) == 1
        assert querier.orders[0] is not None

    def test_order_by_modified_at_ascending(self) -> None:
        """Test ordering by modified_at ascending"""
        request = SearchKeyPairsRequest(
            order=[
                KeyPairOrder(
                    field=KeyPairOrderField.MODIFIED_AT,
                    direction=OrderDirection.ASC,
                )
            ]
        )
        adapter = KeyPairAdapter()
        querier = adapter.build_querier(request)

        assert len(querier.orders) == 1
        assert querier.orders[0] is not None

    def test_order_by_modified_at_descending(self) -> None:
        """Test ordering by modified_at descending"""
        request = SearchKeyPairsRequest(
            order=[
                KeyPairOrder(
                    field=KeyPairOrderField.MODIFIED_AT,
                    direction=OrderDirection.DESC,
                )
            ]
        )
        adapter = KeyPairAdapter()
        querier = adapter.build_querier(request)

        assert len(querier.orders) == 1
        assert querier.orders[0] is not None

    def test_order_by_last_used_ascending(self) -> None:
        """Test ordering by last_used ascending"""
        request = SearchKeyPairsRequest(
            order=[
                KeyPairOrder(
                    field=KeyPairOrderField.LAST_USED,
                    direction=OrderDirection.ASC,
                )
            ]
        )
        adapter = KeyPairAdapter()
        querier = adapter.build_querier(request)

        assert len(querier.orders) == 1
        assert querier.orders[0] is not None

    def test_order_by_last_used_descending(self) -> None:
        """Test ordering by last_used descending"""
        request = SearchKeyPairsRequest(
            order=[
                KeyPairOrder(
                    field=KeyPairOrderField.LAST_USED,
                    direction=OrderDirection.DESC,
                )
            ]
        )
        adapter = KeyPairAdapter()
        querier = adapter.build_querier(request)

        assert len(querier.orders) == 1
        assert querier.orders[0] is not None

    def test_order_by_rate_limit_ascending(self) -> None:
        """Test ordering by rate_limit ascending"""
        request = SearchKeyPairsRequest(
            order=[
                KeyPairOrder(
                    field=KeyPairOrderField.RATE_LIMIT,
                    direction=OrderDirection.ASC,
                )
            ]
        )
        adapter = KeyPairAdapter()
        querier = adapter.build_querier(request)

        assert len(querier.orders) == 1
        assert querier.orders[0] is not None

    def test_order_by_rate_limit_descending(self) -> None:
        """Test ordering by rate_limit descending"""
        request = SearchKeyPairsRequest(
            order=[
                KeyPairOrder(
                    field=KeyPairOrderField.RATE_LIMIT,
                    direction=OrderDirection.DESC,
                )
            ]
        )
        adapter = KeyPairAdapter()
        querier = adapter.build_querier(request)

        assert len(querier.orders) == 1
        assert querier.orders[0] is not None

    def test_order_by_num_queries_ascending(self) -> None:
        """Test ordering by num_queries ascending"""
        request = SearchKeyPairsRequest(
            order=[
                KeyPairOrder(
                    field=KeyPairOrderField.NUM_QUERIES,
                    direction=OrderDirection.ASC,
                )
            ]
        )
        adapter = KeyPairAdapter()
        querier = adapter.build_querier(request)

        assert len(querier.orders) == 1
        assert querier.orders[0] is not None

    def test_order_by_num_queries_descending(self) -> None:
        """Test ordering by num_queries descending"""
        request = SearchKeyPairsRequest(
            order=[
                KeyPairOrder(
                    field=KeyPairOrderField.NUM_QUERIES,
                    direction=OrderDirection.DESC,
                )
            ]
        )
        adapter = KeyPairAdapter()
        querier = adapter.build_querier(request)

        assert len(querier.orders) == 1
        assert querier.orders[0] is not None

    def test_pagination(self) -> None:
        """Test pagination parameters"""
        request = SearchKeyPairsRequest(limit=10, offset=5)
        adapter = KeyPairAdapter()
        querier = adapter.build_querier(request)

        assert querier.pagination is not None
        assert isinstance(querier.pagination, OffsetPagination)
        assert querier.pagination.limit == 10
        assert querier.pagination.offset == 5

    def test_filter_order_pagination_combined(self) -> None:
        """Test filter, order, and pagination all combined"""
        request = SearchKeyPairsRequest(
            filter=KeyPairFilter(
                user_id=StringFilter(contains="user"),
                is_active=True,
            ),
            order=[
                KeyPairOrder(
                    field=KeyPairOrderField.CREATED_AT,
                    direction=OrderDirection.DESC,
                )
            ],
            limit=20,
            offset=10,
        )
        adapter = KeyPairAdapter()
        querier = adapter.build_querier(request)

        assert len(querier.conditions) == 2
        assert len(querier.orders) == 1
        assert querier.pagination is not None
        assert isinstance(querier.pagination, OffsetPagination)
        assert querier.pagination.limit == 20
        assert querier.pagination.offset == 10


class TestKeyPairAdapterConversion:
    """Test cases for KeyPairAdapter.convert_to_dto"""

    def test_convert_to_dto(self) -> None:
        """Test converting KeyPairData to KeyPairDTO"""
        now = datetime.now(tz=UTC)
        user_uuid = uuid.uuid4()

        data = KeyPairData(
            user_id=user_uuid,
            access_key=AccessKey("AKIAIOSFODNN7EXAMPLE"),
            secret_key=SecretKey("wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"),
            is_active=True,
            is_admin=False,
            created_at=now,
            modified_at=now,
            resource_policy_name="default",
            rate_limit=1000,
            ssh_public_key="ssh-rsa AAAA...",
            ssh_private_key="-----BEGIN RSA PRIVATE KEY-----...",
            dotfiles=b"\x90",
            bootstrap_script="",
        )

        adapter = KeyPairAdapter()
        dto = adapter.convert_to_dto(data)

        assert isinstance(dto, KeyPairDTO)
        assert dto.access_key == "AKIAIOSFODNN7EXAMPLE"
        assert dto.secret_key == "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
        assert dto.user_id is None
        assert dto.user_uuid == user_uuid
        assert dto.is_active is True
        assert dto.is_admin is False
        assert dto.created_at == now
        assert dto.modified_at == now
        assert dto.last_used is None
        assert dto.resource_policy == "default"
        assert dto.rate_limit == 1000
        assert dto.num_queries == 0


class TestKeyPairAdapterUpdater:
    """Test cases for KeyPairAdapter.build_updater"""

    def test_build_updater_all_fields(self) -> None:
        """Test building updater with all fields updated"""
        request = UpdateKeyPairRequest(
            is_active=False,
            is_admin=True,
            resource_policy="custom-policy",
            rate_limit=500,
        )
        access_key = "AKIAIOSFODNN7EXAMPLE"

        adapter = KeyPairAdapter()
        updater = adapter.build_updater(request, access_key)
        spec = cast(KeyPairUpdaterSpec, updater.spec)

        assert spec.is_active.value() is False
        assert spec.is_admin.value() is True
        assert spec.resource_policy.value() == "custom-policy"
        assert spec.rate_limit.value() == 500
        assert updater.pk_value == access_key

    def test_build_updater_partial_fields(self) -> None:
        """Test building updater with only some fields updated"""
        request = UpdateKeyPairRequest(
            is_active=False,
            rate_limit=200,
        )
        access_key = "AKIAIOSFODNN7EXAMPLE"

        adapter = KeyPairAdapter()
        updater = adapter.build_updater(request, access_key)
        spec = cast(KeyPairUpdaterSpec, updater.spec)

        assert spec.is_active.value() is False
        assert spec.is_admin.optional_value() is None
        assert spec.resource_policy.optional_value() is None
        assert spec.rate_limit.value() == 200
        assert updater.pk_value == access_key

    def test_build_updater_no_fields(self) -> None:
        """Test building updater with no fields updated"""
        request = UpdateKeyPairRequest()
        access_key = "AKIAIOSFODNN7EXAMPLE"

        adapter = KeyPairAdapter()
        updater = adapter.build_updater(request, access_key)
        spec = cast(KeyPairUpdaterSpec, updater.spec)

        assert spec.is_active.optional_value() is None
        assert spec.is_admin.optional_value() is None
        assert spec.resource_policy.optional_value() is None
        assert spec.rate_limit.optional_value() is None
        assert updater.pk_value == access_key

    def test_build_updater_pk_value_is_access_key(self) -> None:
        """Test that pk_value is the access key"""
        request = UpdateKeyPairRequest(is_active=True)
        access_key = "AKIAIOSFODNN7EXAMPLE"

        adapter = KeyPairAdapter()
        updater = adapter.build_updater(request, access_key)

        assert updater.pk_value == access_key
