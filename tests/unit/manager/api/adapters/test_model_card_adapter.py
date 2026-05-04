"""Unit tests for v2 ModelCardAdapter delete option propagation."""

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


@dataclass(frozen=True)
class DeleteCase:
    """Parameter set for delete-options propagation tests."""

    options: DeleteModelCardOptions


_DELETE_CASES = [
    pytest.param(DeleteCase(options=DeleteModelCardOptions()), id="option_off"),
    pytest.param(
        DeleteCase(options=DeleteModelCardOptions(delete_associated_vfolder=True)),
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
    """Tests for ModelCardAdapter.delete() option propagation.

    The adapter no longer orchestrates vfolder deletion itself — the option
    is forwarded to the service/repository layer which handles the model card
    delete and the vfolder trash in a single DB transaction. These tests
    verify that the option lands on ``DeleteModelCardAction`` unchanged.
    """

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
        return processors

    @pytest.fixture
    def adapter(self, mock_processors: MagicMock) -> ModelCardAdapter:
        return ModelCardAdapter(mock_processors)

    @pytest.mark.parametrize("case", _DELETE_CASES)
    async def test_delete_forwards_options_on_action(
        self,
        adapter: ModelCardAdapter,
        mock_processors: MagicMock,
        card_id: uuid.UUID,
        case: DeleteCase,
    ) -> None:
        payload = await adapter.delete(card_id, options=case.options)

        assert payload.id == card_id
        mock_processors.model_card.delete.wait_for_complete.assert_awaited_once_with(
            DeleteModelCardAction(id=card_id, options=case.options)
        )


class TestModelCardAdapterBulkDelete:
    """Tests for ModelCardAdapter.bulk_delete() option propagation."""

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
        return processors

    @pytest.fixture
    def adapter(self, mock_processors: MagicMock) -> ModelCardAdapter:
        return ModelCardAdapter(mock_processors)

    @pytest.mark.parametrize("case", _DELETE_CASES)
    async def test_bulk_delete_forwards_options_per_action(
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
        called_actions = [
            call.args[0]
            for call in mock_processors.model_card.delete.wait_for_complete.await_args_list
        ]
        assert called_actions == [
            DeleteModelCardAction(id=card_id, options=case.options) for card_id in ids
        ]
