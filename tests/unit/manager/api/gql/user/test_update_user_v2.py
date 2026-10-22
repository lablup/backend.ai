from __future__ import annotations

import uuid
from collections.abc import Iterator
from typing import Any, cast
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ai.backend.common.contexts.user import with_user
from ai.backend.common.data.user.types import UserData, UserRole
from ai.backend.manager.api.gql.user.resolver.mutation import update_user_v2
from ai.backend.manager.api.gql.user.types.inputs import UpdateUserV2InputGQL
from ai.backend.manager.api.gql.user.types.payloads import UpdateUserPayloadGQL
from ai.backend.manager.errors.user import UserModificationBadRequest


def _user(role: UserRole) -> UserData:
    is_superadmin = role == UserRole.SUPERADMIN
    return UserData(
        user_id=uuid.uuid4(),
        is_authorized=True,
        is_admin=is_superadmin,
        is_superadmin=is_superadmin,
        role=role,
        domain_name="default",
    )


class TestUpdateUserV2:
    @pytest.fixture
    def mock_info(self) -> MagicMock:
        info = MagicMock()
        info.context.adapters.user.modify_user_by_id = AsyncMock()
        return info

    @pytest.fixture
    def stub_payload(self) -> Iterator[None]:
        with patch.object(UpdateUserPayloadGQL, "from_pydantic"):
            yield

    @pytest.mark.usefixtures("stub_payload")
    @pytest.mark.parametrize("role", [UserRole.USER, UserRole.SUPERADMIN])
    async def test_own_password_change_clears_need_password_change(
        self, mock_info: MagicMock, role: UserRole
    ) -> None:
        with with_user(_user(role)):
            await cast(Any, update_user_v2).base_resolver(
                mock_info, UpdateUserV2InputGQL(password="new-password")
            )
        _, dto = mock_info.context.adapters.user.modify_user_by_id.await_args.args
        assert dto.need_password_change is False

    @pytest.mark.usefixtures("stub_payload")
    async def test_update_without_password_leaves_need_password_change(
        self, mock_info: MagicMock
    ) -> None:
        with with_user(_user(UserRole.USER)):
            await cast(Any, update_user_v2).base_resolver(
                mock_info, UpdateUserV2InputGQL(full_name="New Name")
            )
        _, dto = mock_info.context.adapters.user.modify_user_by_id.await_args.args
        assert "need_password_change" not in dto.model_fields_set

    async def test_own_password_change_requiring_change_rejected(
        self, mock_info: MagicMock
    ) -> None:
        with (
            with_user(_user(UserRole.SUPERADMIN)),
            pytest.raises(UserModificationBadRequest),
        ):
            await cast(Any, update_user_v2).base_resolver(
                mock_info,
                UpdateUserV2InputGQL(password="new-password", need_password_change=True),
            )
        mock_info.context.adapters.user.modify_user_by_id.assert_not_awaited()
