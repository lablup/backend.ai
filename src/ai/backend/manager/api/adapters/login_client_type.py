"""Login client type adapter bridging DTOs and Processors."""

from __future__ import annotations

from uuid import UUID

from ai.backend.common.api_handlers import Sentinel
from ai.backend.common.dto.manager.v2.login_client_type.request import (
    CreateLoginClientTypeInput,
    UpdateLoginClientTypeInput,
)
from ai.backend.common.dto.manager.v2.login_client_type.response import (
    CreateLoginClientTypePayload,
    DeleteLoginClientTypePayload,
    ListLoginClientTypesPayload,
    LoginClientTypeNode,
    UpdateLoginClientTypePayload,
)
from ai.backend.manager.data.login_client_type.types import LoginClientTypeData
from ai.backend.manager.services.login_client_type.actions.create import (
    CreateLoginClientTypeAction,
)
from ai.backend.manager.services.login_client_type.actions.delete import (
    DeleteLoginClientTypeAction,
)
from ai.backend.manager.services.login_client_type.actions.get import (
    GetLoginClientTypeAction,
)
from ai.backend.manager.services.login_client_type.actions.list import (
    ListLoginClientTypesAction,
)
from ai.backend.manager.services.login_client_type.actions.update import (
    UpdateLoginClientTypeAction,
)

from .base import BaseAdapter


class LoginClientTypeAdapter(BaseAdapter):
    """Adapter for login client type domain operations."""

    async def admin_create(self, input: CreateLoginClientTypeInput) -> CreateLoginClientTypePayload:
        action_result = await self._processors.auth.create_login_client_type.wait_for_complete(
            CreateLoginClientTypeAction(
                name=input.name,
                description=input.description,
            )
        )
        return CreateLoginClientTypePayload(
            login_client_type=self._data_to_node(action_result.login_client_type),
        )

    async def get(self, type_id: UUID) -> LoginClientTypeNode:
        action_result = await self._processors.auth.get_login_client_type.wait_for_complete(
            GetLoginClientTypeAction(id=type_id, name=None)
        )
        return self._data_to_node(action_result.login_client_type)

    async def get_by_name(self, name: str) -> LoginClientTypeNode:
        action_result = await self._processors.auth.get_login_client_type.wait_for_complete(
            GetLoginClientTypeAction(id=None, name=name)
        )
        return self._data_to_node(action_result.login_client_type)

    async def list_all(self) -> ListLoginClientTypesPayload:
        action_result = await self._processors.auth.list_login_client_types.wait_for_complete(
            ListLoginClientTypesAction()
        )
        return ListLoginClientTypesPayload(
            items=[self._data_to_node(item) for item in action_result.login_client_types],
        )

    async def admin_update(
        self, type_id: UUID, input: UpdateLoginClientTypeInput
    ) -> UpdateLoginClientTypePayload:
        raw_description = input.description
        if isinstance(raw_description, Sentinel):
            description_set = False
            description_value: str | None = None
        else:
            description_set = True
            description_value = raw_description
        action_result = await self._processors.auth.update_login_client_type.wait_for_complete(
            UpdateLoginClientTypeAction(
                id=type_id,
                name=input.name,
                description_set=description_set,
                description=description_value,
            )
        )
        return UpdateLoginClientTypePayload(
            login_client_type=self._data_to_node(action_result.login_client_type),
        )

    async def admin_delete(self, type_id: UUID) -> DeleteLoginClientTypePayload:
        action_result = await self._processors.auth.delete_login_client_type.wait_for_complete(
            DeleteLoginClientTypeAction(id=type_id)
        )
        return DeleteLoginClientTypePayload(id=action_result.login_client_type.id)

    @staticmethod
    def _data_to_node(data: LoginClientTypeData) -> LoginClientTypeNode:
        return LoginClientTypeNode(
            id=data.id,
            name=data.name,
            description=data.description,
            created_at=data.created_at,
            modified_at=data.modified_at,
        )
