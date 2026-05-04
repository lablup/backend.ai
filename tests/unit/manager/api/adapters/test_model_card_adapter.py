"""Unit tests for v2 ModelCardAdapter delete orchestration."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from ai.backend.common.dto.manager.v2.model_card.request import (
    DeleteModelCardOptions,
    DeleteModelCardsInput,
)
from ai.backend.common.identifier.vfolder import VFolderUUID
from ai.backend.manager.api.adapters.model_card.adapter import ModelCardAdapter
from ai.backend.manager.data.model_card.types import ModelCardData
from ai.backend.manager.services.model_card.actions.delete import (
    DeleteModelCardAction,
    DeleteModelCardActionResult,
)
from ai.backend.manager.services.vfolder.actions.vfolder_v2 import DeleteVFolderV2Action


@dataclass(frozen=True)
class DeleteCase:
    """Parameter set for delete-with-vfolder orchestration tests."""

    options: DeleteModelCardOptions
    expects_vfolder_delete: bool


_DELETE_CASES = [
    pytest.param(
        DeleteCase(options=DeleteModelCardOptions(), expects_vfolder_delete=False),
        id="option_off",
    ),
    pytest.param(
        DeleteCase(
            options=DeleteModelCardOptions(delete_associated_vfolder=True),
            expects_vfolder_delete=True,
        ),
        id="option_on",
    ),
]


def _create_model_card_data(
    card_id: uuid.UUID,
    vfolder_id: VFolderUUID,
) -> ModelCardData:
    now = datetime.now(tz=UTC)
    return ModelCardData(
        id=card_id,
        name="test-card",
        vfolder_id=vfolder_id,
        domain="default",
        project_id=uuid4(),
        creator_id=uuid4(),
        author=None,
        title=None,
        model_version=None,
        description=None,
        task=None,
        category=None,
        architecture=None,
        framework=[],
        label=[],
        license=None,
        min_resource=[],
        readme=None,
        access_level="internal",
        created_at=now,
        updated_at=None,
    )


class TestModelCardAdapterDelete:
    """Tests for ModelCardAdapter.delete() option orchestration."""

    @pytest.fixture
    def card_id(self) -> uuid.UUID:
        return uuid4()

    @pytest.fixture
    def vfolder_id(self) -> VFolderUUID:
        return VFolderUUID(uuid4())

    @pytest.fixture
    def mock_processors(
        self,
        card_id: uuid.UUID,
        vfolder_id: VFolderUUID,
    ) -> MagicMock:
        processors = MagicMock()
        processors.model_card.delete.wait_for_complete = AsyncMock(
            return_value=DeleteModelCardActionResult(
                model_card=_create_model_card_data(card_id, vfolder_id)
            ),
        )
        processors.vfolder.delete_v2.wait_for_complete = AsyncMock(return_value=None)
        return processors

    @pytest.fixture
    def adapter(self, mock_processors: MagicMock) -> ModelCardAdapter:
        return ModelCardAdapter(mock_processors)

    @pytest.mark.parametrize("case", _DELETE_CASES)
    async def test_delete_orchestrates_vfolder_per_option(
        self,
        adapter: ModelCardAdapter,
        mock_processors: MagicMock,
        card_id: uuid.UUID,
        vfolder_id: VFolderUUID,
        case: DeleteCase,
    ) -> None:
        payload = await adapter.delete(card_id, options=case.options)

        assert payload.id == card_id
        mock_processors.model_card.delete.wait_for_complete.assert_awaited_once_with(
            DeleteModelCardAction(id=card_id)
        )
        if case.expects_vfolder_delete:
            mock_processors.vfolder.delete_v2.wait_for_complete.assert_awaited_once_with(
                DeleteVFolderV2Action(vfolder_id=vfolder_id)
            )
        else:
            mock_processors.vfolder.delete_v2.wait_for_complete.assert_not_called()


class TestModelCardAdapterBulkDelete:
    """Tests for ModelCardAdapter.bulk_delete() option orchestration."""

    @pytest.fixture
    def card_pairs(self) -> list[tuple[uuid.UUID, VFolderUUID]]:
        return [(uuid4(), VFolderUUID(uuid4())) for _ in range(3)]

    @pytest.fixture
    def mock_processors(
        self,
        card_pairs: list[tuple[uuid.UUID, VFolderUUID]],
    ) -> MagicMock:
        results = [
            DeleteModelCardActionResult(model_card=_create_model_card_data(card_id, vfolder_id))
            for card_id, vfolder_id in card_pairs
        ]
        processors = MagicMock()
        processors.model_card.delete.wait_for_complete = AsyncMock(side_effect=results)
        processors.vfolder.delete_v2.wait_for_complete = AsyncMock(return_value=None)
        return processors

    @pytest.fixture
    def adapter(self, mock_processors: MagicMock) -> ModelCardAdapter:
        return ModelCardAdapter(mock_processors)

    @pytest.mark.parametrize("case", _DELETE_CASES)
    async def test_bulk_delete_orchestrates_vfolder_per_option(
        self,
        adapter: ModelCardAdapter,
        mock_processors: MagicMock,
        card_pairs: list[tuple[uuid.UUID, VFolderUUID]],
        case: DeleteCase,
    ) -> None:
        ids = [card_id for card_id, _ in card_pairs]

        payload = await adapter.bulk_delete(DeleteModelCardsInput(ids=ids), case.options)

        assert payload.deleted_count == len(ids)
        assert mock_processors.model_card.delete.wait_for_complete.await_count == len(ids)
        if case.expects_vfolder_delete:
            called_vfolder_ids = [
                call.args[0].vfolder_id
                for call in mock_processors.vfolder.delete_v2.wait_for_complete.await_args_list
            ]
            assert called_vfolder_ids == [vfolder_id for _, vfolder_id in card_pairs]
        else:
            mock_processors.vfolder.delete_v2.wait_for_complete.assert_not_called()
