from __future__ import annotations

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.common.data.entity.entity_share import EntityShareID
from ai.backend.common.data.entity.project import ProjectEntityType
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.data.entity.vfolder import VFolderEntityType
from ai.backend.common.dto.manager.v2.entity_share.response import EntityShareNode
from ai.backend.common.dto.manager.v2.entity_share.types import EntityShareStatusDTO
from ai.backend.common.dto.manager.v2.rbac.types import PermissionBitDTO
from ai.backend.manager.api.gql.base import StringFilter, UUIDFilter
from ai.backend.manager.api.gql.entity_share.types import (
    EntityShareFilterGQL,
    EntityShareGQL,
    EntityShareStatusFilterGQL,
)
from ai.backend.manager.errors.common import GenericBadRequest
from ai.backend.manager.errors.permission import NotEnoughPermission

_NOW = datetime(2026, 1, 1, tzinfo=UTC)


def _share(
    sharer_user_id: UserID | None = None,
    recipient_entity_id: uuid.UUID | None = None,
    recipient_email: str | None = None,
    target_entity_id: uuid.UUID | None = None,
) -> EntityShareGQL:
    return EntityShareGQL.from_pydantic(
        EntityShareNode(
            id=EntityShareID(uuid.uuid4()),
            entity_id=uuid.uuid4(),
            sharer_user_id=sharer_user_id,
            recipient_entity_type=ProjectEntityType() if recipient_entity_id else None,
            recipient_entity_id=recipient_entity_id,
            recipient_email=recipient_email,
            target_entity_type=VFolderEntityType(),
            target_entity_id=target_entity_id or uuid.uuid4(),
            permissions=[PermissionBitDTO.READ],
            status=EntityShareStatusDTO.PENDING,
            created_at=_NOW,
            updated_at=_NOW,
        )
    )


class TestEntityShareSharer:
    @pytest.fixture
    def mock_info(self) -> MagicMock:
        return MagicMock()

    async def test_sharer_is_loaded_by_sharer_user_id(self, mock_info: MagicMock) -> None:
        sharer_user_id = UserID(uuid.uuid4())
        user_node = MagicMock()
        mock_info.context.data_loaders.user_loader.load = AsyncMock(return_value=user_node)

        result = await _share(sharer_user_id).sharer(info=mock_info)

        assert result is user_node
        mock_info.context.data_loaders.user_loader.load.assert_awaited_once_with(sharer_user_id)

    async def test_deleted_sharer_resolves_to_none_without_loading(
        self, mock_info: MagicMock
    ) -> None:
        mock_info.context.data_loaders.user_loader.load = AsyncMock()

        result = await _share(None).sharer(info=mock_info)

        assert result is None
        mock_info.context.data_loaders.user_loader.load.assert_not_awaited()

    async def test_unreadable_sharer_raises_the_permission_error(
        self, mock_info: MagicMock
    ) -> None:
        mock_info.context.data_loaders.user_loader.load = AsyncMock(
            side_effect=NotEnoughPermission()
        )

        with pytest.raises(NotEnoughPermission):
            await _share(UserID(uuid.uuid4())).sharer(info=mock_info)


class TestEntityShareRecipientEntity:
    @pytest.fixture
    def mock_info(self) -> MagicMock:
        info = MagicMock()
        loaders = info.context.data_loaders
        loaders.entity_node_loader.load = AsyncMock()
        loaders.user_id_by_email_loader.load = AsyncMock()
        loaders.user_loader.load = AsyncMock()
        return info

    async def test_named_recipient_is_loaded_as_its_entity(self, mock_info: MagicMock) -> None:
        project_id = uuid.uuid4()
        loaders = mock_info.context.data_loaders

        await _share(recipient_entity_id=project_id).recipient_entity(info=mock_info)

        loaded_id = loaders.entity_node_loader.load.call_args.args[0]
        assert isinstance(loaded_id.entity_type(), ProjectEntityType)
        assert loaded_id == project_id
        loaders.user_id_by_email_loader.load.assert_not_awaited()

    async def test_address_is_loaded_as_the_user_holding_it(self, mock_info: MagicMock) -> None:
        user_id = UserID(uuid.uuid4())
        user_node = MagicMock()
        loaders = mock_info.context.data_loaders
        loaders.user_id_by_email_loader.load.return_value = user_id
        loaders.user_loader.load.return_value = user_node

        result = await _share(recipient_email="to@example.com").recipient_entity(info=mock_info)

        assert result is user_node
        loaders.user_id_by_email_loader.load.assert_awaited_once_with("to@example.com")
        loaders.user_loader.load.assert_awaited_once_with(user_id)

    async def test_unresolvable_address_raises_the_lookup_error(self, mock_info: MagicMock) -> None:
        loaders = mock_info.context.data_loaders
        loaders.user_id_by_email_loader.load.side_effect = GenericBadRequest()

        with pytest.raises(GenericBadRequest):
            await _share(recipient_email="to@example.com").recipient_entity(info=mock_info)

        loaders.user_loader.load.assert_not_awaited()

    async def test_no_recipient_resolves_to_none(self, mock_info: MagicMock) -> None:
        result = await _share().recipient_entity(info=mock_info)

        assert result is None
        mock_info.context.data_loaders.entity_node_loader.load.assert_not_awaited()


class TestEntityShareTargetEntity:
    async def test_target_is_loaded_as_its_entity(self) -> None:
        target_id = uuid.uuid4()
        mock_info = MagicMock()
        mock_info.context.data_loaders.entity_node_loader.load = AsyncMock()

        await _share(target_entity_id=target_id).target_entity(info=mock_info)

        loaded_id = mock_info.context.data_loaders.entity_node_loader.load.call_args.args[0]
        assert isinstance(loaded_id.entity_type(), VFolderEntityType)
        assert loaded_id == target_id


class TestEntityShareFilterToPydantic:
    def test_status_equals(self) -> None:
        filter_gql = EntityShareFilterGQL(
            status=EntityShareStatusFilterGQL(equals=EntityShareStatusDTO.ACCEPTED)
        )

        dto = filter_gql.to_pydantic()

        assert dto.status is not None
        assert dto.status.equals == EntityShareStatusDTO.ACCEPTED

    def test_status_in(self) -> None:
        statuses = [EntityShareStatusDTO.PENDING, EntityShareStatusDTO.ACCEPTED]
        filter_gql = EntityShareFilterGQL(status=EntityShareStatusFilterGQL(in_=statuses))

        dto = filter_gql.to_pydantic()

        assert dto.status is not None
        assert dto.status.in_ == statuses

    def test_recipient_entity_id(self) -> None:
        recipient_id = uuid.uuid4()
        filter_gql = EntityShareFilterGQL(recipient_entity_id=UUIDFilter(equals=recipient_id))

        dto = filter_gql.to_pydantic()

        assert dto.recipient_entity_id is not None
        assert dto.recipient_entity_id.equals == recipient_id

    def test_target_entity_id(self) -> None:
        target_id = uuid.uuid4()
        filter_gql = EntityShareFilterGQL(target_entity_id=UUIDFilter(equals=target_id))

        dto = filter_gql.to_pydantic()

        assert dto.target_entity_id is not None
        assert dto.target_entity_id.equals == target_id

    def test_recipient_email(self) -> None:
        filter_gql = EntityShareFilterGQL(recipient_email=StringFilter(contains="example"))

        dto = filter_gql.to_pydantic()

        assert dto.recipient_email is not None
        assert dto.recipient_email.contains == "example"
