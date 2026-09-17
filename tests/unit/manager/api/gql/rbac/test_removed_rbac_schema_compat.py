"""Tests for the deprecated RBAC schema members kept so older clients can detect them."""

from __future__ import annotations

import uuid
from collections.abc import Generator
from datetime import UTC, datetime
from typing import Any, cast
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ai.backend.common.data.entity.types import EntityType
from ai.backend.common.dto.manager.v2.rbac.types import PermissionBitDTO
from ai.backend.common.exception import DeprecatedAPI
from ai.backend.manager.api.gql.rbac.resolver import entity as entity_resolver
from ai.backend.manager.api.gql.rbac.resolver import role_invitation as role_invitation_resolver
from ai.backend.manager.api.gql.rbac.types.permission import (
    CreatePermissionInput,
    OperationTypeGQL,
    PermissionGQL,
)
from ai.backend.manager.api.gql.rbac.types.role_invitation import (
    AcceptRoleInvitationInputGQL,
    CancelRoleInvitationInputGQL,
    CreateRoleInvitationInputGQL,
    RejectRoleInvitationInputGQL,
)
from ai.backend.manager.api.gql.rbac.types.scope import PermissionBitGQL, RBACElementTypeGQL
from ai.backend.manager.api.gql.role_preset.types.node import RolePresetGQL
from ai.backend.manager.api.gql.role_preset.types.permission import (
    RolePermissionPresetOrderByGQL,
    RolePermissionPresetOrderFieldGQL,
)


@pytest.fixture(autouse=True)
def _bypass_admin_check() -> Generator[None]:
    with (
        patch("ai.backend.manager.api.gql.rbac.resolver.role_invitation.check_admin_only"),
        patch("ai.backend.manager.api.gql.rbac.resolver.entity.check_admin_only"),
    ):
        yield


def _resolver(field: object) -> Any:
    return cast(Any, field).base_resolver


class TestRemovedQueries:
    @pytest.mark.parametrize(
        "field",
        [
            pytest.param(role_invitation_resolver.my_role_invitations, id="my"),
            pytest.param(role_invitation_resolver.my_sent_role_invitations, id="my-sent"),
            pytest.param(role_invitation_resolver.admin_role_invitations, id="admin"),
            pytest.param(entity_resolver.admin_entities, id="admin-entities"),
        ],
    )
    async def test_answers_an_empty_connection(self, field: object) -> None:
        connection = await _resolver(field)(info=MagicMock())

        assert connection.edges == []
        assert connection.count == 0

    async def test_role_scoped_answers_an_empty_connection(self) -> None:
        connection = await _resolver(role_invitation_resolver.role_scoped_role_invitations)(
            info=MagicMock(), role_id=uuid.uuid4()
        )

        assert connection.edges == []


class TestRemovedMutations:
    @pytest.mark.parametrize(
        ("field", "input"),
        [
            pytest.param(
                role_invitation_resolver.create_role_invitation,
                CreateRoleInvitationInputGQL(role_id=uuid.uuid4(), emails=["a@example.com"]),
                id="create",
            ),
            pytest.param(
                role_invitation_resolver.accept_role_invitation,
                AcceptRoleInvitationInputGQL(invitation_id=uuid.uuid4()),
                id="accept",
            ),
            pytest.param(
                role_invitation_resolver.reject_role_invitation,
                RejectRoleInvitationInputGQL(invitation_id=uuid.uuid4()),
                id="reject",
            ),
            pytest.param(
                role_invitation_resolver.admin_cancel_role_invitation,
                CancelRoleInvitationInputGQL(invitation_id=uuid.uuid4()),
                id="cancel",
            ),
        ],
    )
    async def test_refuses(self, field: object, input: object) -> None:
        with pytest.raises(DeprecatedAPI):
            await _resolver(field)(info=MagicMock(), input=input)


class TestRemovedPermissionFields:
    def test_output_fields_are_null(self) -> None:
        permission = PermissionGQL(
            id=str(uuid.uuid4()),
            role_id=uuid.uuid4(),
            entity_type="vfolder",
            created_at=datetime.now(UTC),
            permission=PermissionBitGQL.READ,
        )

        assert permission.scope_type() is None
        assert permission.scope_id() is None
        assert permission.operation() is None
        assert permission.scope() is None

    def test_input_fields_are_ignored(self) -> None:
        role_id = uuid.uuid4()
        dto = CreatePermissionInput(
            role_id=role_id,
            entity_type="vfolder",
            permission=PermissionBitGQL.UPDATE,
            scope_type=RBACElementTypeGQL.PROJECT,
            scope_id=str(uuid.uuid4()),
            operation=OperationTypeGQL.GRANT_ALL,
        ).to_pydantic()

        assert dto.role_id == role_id
        assert dto.entity_type == EntityType("vfolder")
        assert dto.permission == PermissionBitDTO.UPDATE


class TestRemovedRolePermissionPresetOrder:
    @pytest.mark.parametrize(
        ("fields", "expected"),
        [
            pytest.param([RolePermissionPresetOrderFieldGQL.OPERATION], None, id="only-operation"),
            pytest.param(
                [
                    RolePermissionPresetOrderFieldGQL.OPERATION,
                    RolePermissionPresetOrderFieldGQL.CREATED_AT,
                ],
                ["created_at"],
                id="operation-dropped",
            ),
        ],
    )
    async def test_operation_order_is_ignored(
        self,
        fields: list[RolePermissionPresetOrderFieldGQL],
        expected: list[str] | None,
    ) -> None:
        now = datetime.now(UTC)
        preset = RolePresetGQL(
            id=str(uuid.uuid4()),
            name="member",
            scope_type="project",
            auto_assign=False,
            deleted=False,
            created_at=now,
            updated_at=now,
        )
        search = AsyncMock()
        search.return_value.items = []
        info = MagicMock()
        info.context.adapters.role_preset.search_permission_presets = search

        await preset.permission_presets(
            info=info,
            order_by=[RolePermissionPresetOrderByGQL(field=field) for field in fields],
        )

        search_input = search.call_args.args[1]
        if expected is None:
            assert search_input.order is None
        else:
            assert [order.field for order in search_input.order] == expected
