from __future__ import annotations

import uuid
from collections.abc import Iterator
from typing import Any, cast
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ai.backend.common.contexts.user import with_user_context
from ai.backend.common.data.entity.domain import DomainID
from ai.backend.common.data.user.types import UserData
from ai.backend.manager.api.gql.user.resolver.mutation import update_user_v2
from ai.backend.manager.api.gql.user.types.enums import UserRoleEnumGQL, UserStatusEnumGQL
from ai.backend.manager.api.gql.user.types.inputs import UpdateUserV2InputGQL
from ai.backend.manager.api.gql.user.types.payloads import UpdateUserPayloadGQL
from ai.backend.manager.errors.auth import InsufficientPrivilege
from ai.backend.manager.errors.user import UserModificationBadRequest
from ai.backend.manager.models.user.row import UserRole

SELF_EDITABLE_INPUTS: list[dict[str, Any]] = [
    {"full_name": "New Name"},
    {"password": "new-password"},
    {"allowed_client_ip": ["10.0.0.0/8"]},
    {"allowed_client_ip": None},
    {"full_name": "New Name", "password": "new-password", "allowed_client_ip": ["10.0.0.1"]},
]

RESTRICTED_INPUTS: list[dict[str, Any]] = [
    {"role": UserRoleEnumGQL.SUPERADMIN},
    {"domain_name": "other"},
    {"resource_policy": "unlimited"},
    {"sudo_session_enabled": True},
    {"container_uid": 0},
    {"full_name": "New Name", "role": UserRoleEnumGQL.ADMIN},
    {"role": None},
]

ALL_FIELDS_INPUT: dict[str, Any] = {
    "username": "renamed",
    "password": "new-password",
    "full_name": "New Name",
    "description": "desc",
    "status": UserStatusEnumGQL.ACTIVE,
    "role": UserRoleEnumGQL.ADMIN,
    "domain_name": "other",
    "group_ids": [uuid.uuid4()],
    "allowed_client_ip": ["10.0.0.1"],
    "need_password_change": False,
    "resource_policy": "unlimited",
    "sudo_session_enabled": True,
    "main_access_key": "AKIAEXAMPLE",
    "container_uid": 1000,
    "container_main_gid": 1000,
    "container_gids": [1000, 1001],
}


def _user(role: UserRole) -> UserData:
    is_superadmin = role == UserRole.SUPERADMIN
    return UserData(
        user_id=uuid.uuid4(),
        is_authorized=True,
        is_admin=is_superadmin,
        is_superadmin=is_superadmin,
        role=role,
        domain_name="default",
        domain_id=DomainID(uuid.uuid4()),
    )


class TestUpdateUserV2:
    @pytest.fixture
    def mock_info(self) -> MagicMock:
        info = MagicMock()
        info.context.adapters.user.update_user_by_id = AsyncMock()
        return info

    @pytest.fixture
    def stub_payload(self) -> Iterator[None]:
        with patch.object(UpdateUserPayloadGQL, "from_pydantic"):
            yield

    @pytest.mark.parametrize("role", [UserRole.USER, UserRole.ADMIN, UserRole.MONITOR])
    @pytest.mark.parametrize("fields", RESTRICTED_INPUTS, ids=lambda f: ",".join(f))
    async def test_non_superadmin_rejected_for_restricted_fields(
        self, mock_info: MagicMock, role: UserRole, fields: dict[str, Any]
    ) -> None:
        with with_user_context(_user(role)), pytest.raises(InsufficientPrivilege):
            await cast(Any, update_user_v2).base_resolver(mock_info, UpdateUserV2InputGQL(**fields))
        mock_info.context.adapters.user.update_user_by_id.assert_not_awaited()

    @pytest.mark.usefixtures("stub_payload")
    @pytest.mark.parametrize("fields", SELF_EDITABLE_INPUTS, ids=lambda f: ",".join(f))
    async def test_non_superadmin_updates_self_editable_fields(
        self, mock_info: MagicMock, fields: dict[str, Any]
    ) -> None:
        me = _user(UserRole.USER)
        with with_user_context(me):
            await cast(Any, update_user_v2).base_resolver(mock_info, UpdateUserV2InputGQL(**fields))
        mock_info.context.adapters.user.update_user_by_id.assert_awaited_once()
        user_id, dto = mock_info.context.adapters.user.update_user_by_id.await_args.args
        assert user_id == me.user_id
        assert dto.model_fields_set - {"need_password_change"} == set(fields)

    @pytest.mark.usefixtures("stub_payload")
    async def test_superadmin_updates_all_fields(self, mock_info: MagicMock) -> None:
        me = _user(UserRole.SUPERADMIN)
        with with_user_context(me):
            await cast(Any, update_user_v2).base_resolver(
                mock_info, UpdateUserV2InputGQL(**ALL_FIELDS_INPUT)
            )
        user_id, dto = mock_info.context.adapters.user.update_user_by_id.await_args.args
        assert user_id == me.user_id
        assert dto.model_fields_set == set(ALL_FIELDS_INPUT)

    @pytest.mark.usefixtures("stub_payload")
    @pytest.mark.parametrize("role", [UserRole.USER, UserRole.SUPERADMIN])
    async def test_own_password_change_clears_need_password_change(
        self, mock_info: MagicMock, role: UserRole
    ) -> None:
        with with_user_context(_user(role)):
            await cast(Any, update_user_v2).base_resolver(
                mock_info, UpdateUserV2InputGQL(password="new-password")
            )
        _, dto = mock_info.context.adapters.user.update_user_by_id.await_args.args
        assert dto.need_password_change is False

    @pytest.mark.usefixtures("stub_payload")
    async def test_update_without_password_leaves_need_password_change(
        self, mock_info: MagicMock
    ) -> None:
        with with_user_context(_user(UserRole.USER)):
            await cast(Any, update_user_v2).base_resolver(
                mock_info, UpdateUserV2InputGQL(full_name="New Name")
            )
        _, dto = mock_info.context.adapters.user.update_user_by_id.await_args.args
        assert "need_password_change" not in dto.model_fields_set

    async def test_own_password_change_requiring_change_rejected(
        self, mock_info: MagicMock
    ) -> None:
        with (
            with_user_context(_user(UserRole.SUPERADMIN)),
            pytest.raises(UserModificationBadRequest),
        ):
            await cast(Any, update_user_v2).base_resolver(
                mock_info,
                UpdateUserV2InputGQL(password="new-password", need_password_change=True),
            )
        mock_info.context.adapters.user.update_user_by_id.assert_not_awaited()
