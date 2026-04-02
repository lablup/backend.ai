from __future__ import annotations

import uuid
from collections.abc import Callable, Generator
from datetime import UTC, datetime
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from ai.backend.manager.api.gql_legacy.vfolder import ModelCard


class TestModelCardParseModelModifiedAt:
    """Tests for ModelCard.parse_model modified_at fallback chain."""

    @pytest.fixture
    def graph_ctx(self) -> MagicMock:
        return MagicMock()

    @pytest.fixture
    def vfolder_row(self) -> MagicMock:
        row = MagicMock()
        row.id = uuid.uuid4()
        row.name = "test-model"
        row.creator = "testuser"
        row.created_at = datetime(2025, 1, 1, tzinfo=UTC)
        row.last_used = datetime(2025, 6, 15, tzinfo=UTC)
        return row

    @pytest.fixture
    def model_def_with_metadata(self) -> Callable[[dict[str, Any]], dict[str, Any]]:
        def _build(metadata: dict[str, Any]) -> dict[str, Any]:
            return {"models": [{"name": "test-model", "metadata": metadata}]}

        return _build

    @pytest.fixture(autouse=True)
    def _mock_vfolder_helpers(self) -> Generator[None]:
        with (
            patch(
                "ai.backend.manager.api.gql_legacy.vfolder.VirtualFolderNode.from_row",
                return_value=MagicMock(),
            ),
            patch(
                "ai.backend.manager.api.gql_legacy.vfolder.VirtualFolder.from_orm_row",
                return_value=MagicMock(),
            ),
        ):
            yield

    async def test_modified_at_uses_metadata_last_modified_when_present(
        self,
        graph_ctx: MagicMock,
        vfolder_row: MagicMock,
        model_def_with_metadata: Callable[[dict[str, Any]], dict[str, Any]],
    ) -> None:
        expected = "2025-12-25T00:00:00Z"
        model_def = model_def_with_metadata({"last_modified": expected})

        card = ModelCard.parse_model(graph_ctx, vfolder_row, model_def=model_def)

        assert card.modified_at == expected

    async def test_modified_at_falls_back_to_last_used_when_metadata_missing(
        self,
        graph_ctx: MagicMock,
        vfolder_row: MagicMock,
        model_def_with_metadata: Callable[[dict[str, Any]], dict[str, Any]],
    ) -> None:
        model_def = model_def_with_metadata({})

        card = ModelCard.parse_model(graph_ctx, vfolder_row, model_def=model_def)

        assert card.modified_at == vfolder_row.last_used

    async def test_modified_at_is_none_when_both_metadata_and_last_used_missing(
        self,
        graph_ctx: MagicMock,
        vfolder_row: MagicMock,
        model_def_with_metadata: Callable[[dict[str, Any]], dict[str, Any]],
    ) -> None:
        vfolder_row.last_used = None
        model_def = model_def_with_metadata({})

        card = ModelCard.parse_model(graph_ctx, vfolder_row, model_def=model_def)

        assert card.modified_at is None
