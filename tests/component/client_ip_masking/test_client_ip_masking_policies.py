"""The masking policies over the real REST stack.

Covers what the unit tests cannot: that the upsert conflicts on ``target_type``
rather than inserting a second row, that the DTO round-trips through the adapter,
and that the login path's read sees what the API wrote.
"""

from __future__ import annotations

import pytest

from ai.backend.client.v2.exceptions import PermissionDeniedError
from ai.backend.client.v2.v2_registry import V2ClientRegistry
from ai.backend.common.dto.manager.v2.client_ip_masking.request import (
    AdminPurgeClientIPMaskingPolicyInput,
    AdminSearchClientIPMaskingPoliciesInput,
    AdminUpsertClientIPMaskingPolicyInput,
    ClientIPMaskingPolicyFilter,
    ClientIPMaskingPolicyOrder,
)
from ai.backend.common.dto.manager.v2.client_ip_masking.types import (
    ClientIPMaskingMode,
    ClientIPMaskingPolicyOrderField,
    ClientIPMaskingTarget,
)
from ai.backend.common.dto.manager.v2.common import OrderDirection
from ai.backend.manager.api.adapter_options.cursor.cursor import encode_cursor
from ai.backend.manager.data.client_ip.masking import (
    ClientIPMaskingMode as ClientIPMaskingModeData,
)
from ai.backend.manager.data.client_ip.masking import (
    ClientIPMaskingTarget as ClientIPMaskingTargetData,
)
from ai.backend.manager.repositories.client_ip_masking.repository import ClientIPMaskingRepository


async def _upsert(
    registry: V2ClientRegistry,
    target_type: ClientIPMaskingTarget,
    mode: ClientIPMaskingMode,
) -> None:
    await registry.client_ip_masking.admin_upsert(
        AdminUpsertClientIPMaskingPolicyInput(target_type=target_type, mode=mode),
    )


class TestClientIPMaskingPoliciesAccess:
    async def test_a_regular_user_cannot_read_the_policies(
        self,
        user_v2_registry: V2ClientRegistry,
    ) -> None:
        with pytest.raises(PermissionDeniedError):
            await user_v2_registry.client_ip_masking.admin_search(
                AdminSearchClientIPMaskingPoliciesInput(),
            )

    async def test_a_regular_user_cannot_change_the_policies(
        self,
        user_v2_registry: V2ClientRegistry,
    ) -> None:
        with pytest.raises(PermissionDeniedError):
            await _upsert(
                user_v2_registry,
                ClientIPMaskingTarget.DEFAULT,
                ClientIPMaskingMode.TRUNCATE,
            )


class TestClientIPMaskingPoliciesCrud:
    async def test_nothing_is_set_to_begin_with(
        self,
        admin_v2_registry: V2ClientRegistry,
    ) -> None:
        result = await admin_v2_registry.client_ip_masking.admin_search(
            AdminSearchClientIPMaskingPoliciesInput(),
        )

        assert result.items == []
        assert result.total_count == 0

    async def test_an_upsert_is_read_back(
        self,
        admin_v2_registry: V2ClientRegistry,
    ) -> None:
        await _upsert(
            admin_v2_registry,
            ClientIPMaskingTarget.LOGIN_HISTORY,
            ClientIPMaskingMode.TRUNCATE,
        )

        result = await admin_v2_registry.client_ip_masking.admin_search(
            AdminSearchClientIPMaskingPoliciesInput(),
        )

        assert [(item.target_type, item.mode) for item in result.items] == [
            (ClientIPMaskingTarget.LOGIN_HISTORY, ClientIPMaskingMode.TRUNCATE)
        ]

    async def test_upserting_the_same_target_replaces_its_row(
        self,
        admin_v2_registry: V2ClientRegistry,
    ) -> None:
        """The conflict is on ``target_type``: a target holds one policy, not a history."""
        first = await admin_v2_registry.client_ip_masking.admin_upsert(
            AdminUpsertClientIPMaskingPolicyInput(
                target_type=ClientIPMaskingTarget.DEFAULT,
                mode=ClientIPMaskingMode.TRUNCATE,
            ),
        )
        second = await admin_v2_registry.client_ip_masking.admin_upsert(
            AdminUpsertClientIPMaskingPolicyInput(
                target_type=ClientIPMaskingTarget.DEFAULT,
                mode=ClientIPMaskingMode.NONE,
            ),
        )

        assert second.policy.id == first.policy.id
        assert second.policy.mode == ClientIPMaskingMode.NONE

        result = await admin_v2_registry.client_ip_masking.admin_search(
            AdminSearchClientIPMaskingPoliciesInput(),
        )
        assert result.total_count == 1

    async def test_each_target_holds_its_own_row(
        self,
        admin_v2_registry: V2ClientRegistry,
    ) -> None:
        await _upsert(
            admin_v2_registry,
            ClientIPMaskingTarget.DEFAULT,
            ClientIPMaskingMode.TRUNCATE,
        )
        await _upsert(
            admin_v2_registry,
            ClientIPMaskingTarget.LOGIN_HISTORY,
            ClientIPMaskingMode.NONE,
        )

        result = await admin_v2_registry.client_ip_masking.admin_search(
            AdminSearchClientIPMaskingPoliciesInput(),
        )

        assert result.total_count == 2
        assert {item.target_type: item.mode for item in result.items} == {
            ClientIPMaskingTarget.DEFAULT: ClientIPMaskingMode.TRUNCATE,
            ClientIPMaskingTarget.LOGIN_HISTORY: ClientIPMaskingMode.NONE,
        }

    async def test_the_drop_mode_round_trips(
        self,
        admin_v2_registry: V2ClientRegistry,
    ) -> None:
        """A deployment that must keep no address at all can say so."""
        await _upsert(
            admin_v2_registry,
            ClientIPMaskingTarget.LOGIN_HISTORY,
            ClientIPMaskingMode.DROP,
        )

        result = await admin_v2_registry.client_ip_masking.admin_search(
            AdminSearchClientIPMaskingPoliciesInput(),
        )

        assert [item.mode for item in result.items] == [ClientIPMaskingMode.DROP]

    async def test_a_purged_policy_is_gone(
        self,
        admin_v2_registry: V2ClientRegistry,
    ) -> None:
        created = await admin_v2_registry.client_ip_masking.admin_upsert(
            AdminUpsertClientIPMaskingPolicyInput(
                target_type=ClientIPMaskingTarget.LOGIN_HISTORY,
                mode=ClientIPMaskingMode.TRUNCATE,
            ),
        )

        await admin_v2_registry.client_ip_masking.admin_purge(
            AdminPurgeClientIPMaskingPolicyInput(id=created.policy.id),
        )

        result = await admin_v2_registry.client_ip_masking.admin_search(
            AdminSearchClientIPMaskingPoliciesInput(),
        )
        assert result.items == []


class TestClientIPMaskingPoliciesSearchArguments:
    """filter / order / pagination, the same arguments every other v2 search takes."""

    @pytest.fixture(autouse=True)
    async def both_targets_set(self, admin_v2_registry: V2ClientRegistry) -> None:
        await _upsert(
            admin_v2_registry,
            ClientIPMaskingTarget.DEFAULT,
            ClientIPMaskingMode.TRUNCATE,
        )
        await _upsert(
            admin_v2_registry,
            ClientIPMaskingTarget.LOGIN_HISTORY,
            ClientIPMaskingMode.NONE,
        )

    async def test_filtering_by_target_narrows_the_result(
        self,
        admin_v2_registry: V2ClientRegistry,
    ) -> None:
        result = await admin_v2_registry.client_ip_masking.admin_search(
            AdminSearchClientIPMaskingPoliciesInput(
                filter=ClientIPMaskingPolicyFilter(target_type=ClientIPMaskingTarget.LOGIN_HISTORY),
            ),
        )

        assert [item.target_type for item in result.items] == [ClientIPMaskingTarget.LOGIN_HISTORY]

    async def test_filtering_by_mode_narrows_the_result(
        self,
        admin_v2_registry: V2ClientRegistry,
    ) -> None:
        result = await admin_v2_registry.client_ip_masking.admin_search(
            AdminSearchClientIPMaskingPoliciesInput(
                filter=ClientIPMaskingPolicyFilter(mode=ClientIPMaskingMode.TRUNCATE),
            ),
        )

        assert [item.target_type for item in result.items] == [ClientIPMaskingTarget.DEFAULT]

    async def test_ordering_by_target_type_reverses(
        self,
        admin_v2_registry: V2ClientRegistry,
    ) -> None:
        ascending = await admin_v2_registry.client_ip_masking.admin_search(
            AdminSearchClientIPMaskingPoliciesInput(
                order=[
                    ClientIPMaskingPolicyOrder(
                        field=ClientIPMaskingPolicyOrderField.TARGET_TYPE,
                        direction=OrderDirection.ASC,
                    )
                ],
            ),
        )
        descending = await admin_v2_registry.client_ip_masking.admin_search(
            AdminSearchClientIPMaskingPoliciesInput(
                order=[
                    ClientIPMaskingPolicyOrder(
                        field=ClientIPMaskingPolicyOrderField.TARGET_TYPE,
                        direction=OrderDirection.DESC,
                    )
                ],
            ),
        )

        assert [item.target_type for item in ascending.items] == list(
            reversed([item.target_type for item in descending.items])
        )

    async def test_offset_pagination_splits_the_result(
        self,
        admin_v2_registry: V2ClientRegistry,
    ) -> None:
        first_page = await admin_v2_registry.client_ip_masking.admin_search(
            AdminSearchClientIPMaskingPoliciesInput(limit=1, offset=0),
        )
        second_page = await admin_v2_registry.client_ip_masking.admin_search(
            AdminSearchClientIPMaskingPoliciesInput(limit=1, offset=1),
        )

        assert len(first_page.items) == 1
        assert len(second_page.items) == 1
        assert first_page.items[0].id != second_page.items[0].id
        assert first_page.total_count == 2

    async def test_cursor_pagination_walks_forward(
        self,
        admin_v2_registry: V2ClientRegistry,
    ) -> None:
        first_page = await admin_v2_registry.client_ip_masking.admin_search(
            AdminSearchClientIPMaskingPoliciesInput(first=1),
        )
        assert len(first_page.items) == 1
        assert first_page.has_next_page is True

        second_page = await admin_v2_registry.client_ip_masking.admin_search(
            AdminSearchClientIPMaskingPoliciesInput(
                first=1, after=encode_cursor(first_page.items[0].id)
            ),
        )

        assert len(second_page.items) == 1
        assert second_page.items[0].id != first_page.items[0].id


class TestWhatTheLoginPathResolves:
    """The API writes the row; the login path reads it through the repository."""

    async def test_no_policy_leaves_the_address_alone(
        self,
        masking_repository: ClientIPMaskingRepository,
    ) -> None:
        mode = await masking_repository.resolve_mode(ClientIPMaskingTargetData.LOGIN_HISTORY)

        assert mode == ClientIPMaskingModeData.NONE

    async def test_the_default_applies_where_the_target_has_none(
        self,
        admin_v2_registry: V2ClientRegistry,
        masking_repository: ClientIPMaskingRepository,
    ) -> None:
        await _upsert(
            admin_v2_registry,
            ClientIPMaskingTarget.DEFAULT,
            ClientIPMaskingMode.TRUNCATE,
        )

        mode = await masking_repository.resolve_mode(ClientIPMaskingTargetData.LOGIN_HISTORY)

        assert mode == ClientIPMaskingModeData.TRUNCATE

    async def test_the_target_policy_wins_over_the_default(
        self,
        admin_v2_registry: V2ClientRegistry,
        masking_repository: ClientIPMaskingRepository,
    ) -> None:
        await _upsert(
            admin_v2_registry,
            ClientIPMaskingTarget.DEFAULT,
            ClientIPMaskingMode.TRUNCATE,
        )
        await _upsert(
            admin_v2_registry,
            ClientIPMaskingTarget.LOGIN_HISTORY,
            ClientIPMaskingMode.NONE,
        )

        mode = await masking_repository.resolve_mode(ClientIPMaskingTargetData.LOGIN_HISTORY)

        assert mode == ClientIPMaskingModeData.NONE

    async def test_purging_the_override_falls_back_to_the_default(
        self,
        admin_v2_registry: V2ClientRegistry,
        masking_repository: ClientIPMaskingRepository,
    ) -> None:
        await _upsert(
            admin_v2_registry,
            ClientIPMaskingTarget.DEFAULT,
            ClientIPMaskingMode.TRUNCATE,
        )
        override = await admin_v2_registry.client_ip_masking.admin_upsert(
            AdminUpsertClientIPMaskingPolicyInput(
                target_type=ClientIPMaskingTarget.LOGIN_HISTORY,
                mode=ClientIPMaskingMode.NONE,
            ),
        )

        await admin_v2_registry.client_ip_masking.admin_purge(
            AdminPurgeClientIPMaskingPolicyInput(id=override.policy.id),
        )

        mode = await masking_repository.resolve_mode(ClientIPMaskingTargetData.LOGIN_HISTORY)

        assert mode == ClientIPMaskingModeData.TRUNCATE
