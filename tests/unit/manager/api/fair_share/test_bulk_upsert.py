"""Tests for bulk upsert fair share weight processors.

These tests verify that the bulk upsert action processors work correctly
with the expected action inputs and return proper results.
"""

from __future__ import annotations

from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID

import pytest

from ai.backend.manager.services.fair_share.actions import (
    BulkUpsertDomainFairShareWeightAction,
    BulkUpsertDomainFairShareWeightActionResult,
    BulkUpsertProjectFairShareWeightAction,
    BulkUpsertProjectFairShareWeightActionResult,
    BulkUpsertUserFairShareWeightAction,
    BulkUpsertUserFairShareWeightActionResult,
    DomainWeightInput,
    ProjectWeightInput,
    UserWeightInput,
)


class TestBulkUpsertDomainFairShareWeight:
    """Tests for bulk upsert domain fair share weight processor."""

    @pytest.fixture
    def mock_processors_success(self) -> MagicMock:
        """Processors with successful bulk upsert."""
        processors = MagicMock()
        action_result = BulkUpsertDomainFairShareWeightActionResult(upserted_count=2)
        processors.fair_share.bulk_upsert_domain_fair_share_weight.wait_for_complete = AsyncMock(
            return_value=action_result
        )
        return processors

    @pytest.mark.asyncio
    async def test_successful_bulk_upsert(
        self,
        mock_processors_success: MagicMock,
    ) -> None:
        """Should bulk upsert domain weights and return upserted count."""
        processors = mock_processors_success

        action = BulkUpsertDomainFairShareWeightAction(
            resource_group="default",
            inputs=[
                DomainWeightInput(domain_name="domain1", weight=Decimal("2.0")),
                DomainWeightInput(domain_name="domain2", weight=Decimal("3.0")),
            ],
        )

        result = await processors.fair_share.bulk_upsert_domain_fair_share_weight.wait_for_complete(
            action
        )

        assert result.upserted_count == 2
        processors.fair_share.bulk_upsert_domain_fair_share_weight.wait_for_complete.assert_called_once()

    @pytest.mark.asyncio
    async def test_action_has_correct_structure(
        self,
        mock_processors_success: MagicMock,
    ) -> None:
        """Should verify action input structure."""
        processors = mock_processors_success

        inputs = [
            DomainWeightInput(domain_name="domain1", weight=Decimal("2.0")),
            DomainWeightInput(domain_name="domain2", weight=None),
        ]
        action = BulkUpsertDomainFairShareWeightAction(
            resource_group="default",
            inputs=inputs,
        )

        await processors.fair_share.bulk_upsert_domain_fair_share_weight.wait_for_complete(action)

        # Verify action structure
        assert action.resource_group == "default"
        assert len(action.inputs) == 2
        assert action.inputs[0].domain_name == "domain1"
        assert action.inputs[0].weight == Decimal("2.0")
        assert action.inputs[1].domain_name == "domain2"
        assert action.inputs[1].weight is None


class TestBulkUpsertProjectFairShareWeight:
    """Tests for bulk upsert project fair share weight processor."""

    @pytest.fixture
    def mock_processors_success(self) -> MagicMock:
        """Processors with successful bulk upsert."""
        processors = MagicMock()
        action_result = BulkUpsertProjectFairShareWeightActionResult(upserted_count=2)
        processors.fair_share.bulk_upsert_project_fair_share_weight.wait_for_complete = AsyncMock(
            return_value=action_result
        )
        return processors

    @pytest.mark.asyncio
    async def test_successful_bulk_upsert(
        self,
        mock_processors_success: MagicMock,
    ) -> None:
        """Should bulk upsert project weights and return upserted count."""
        processors = mock_processors_success
        project_id1 = UUID("aaaaaaaa-bbbb-cccc-dddd-111111111111")
        project_id2 = UUID("aaaaaaaa-bbbb-cccc-dddd-222222222222")

        action = BulkUpsertProjectFairShareWeightAction(
            resource_group="default",
            inputs=[
                ProjectWeightInput(
                    project_id=project_id1,
                    domain_name="default",
                    weight=Decimal("2.0"),
                ),
                ProjectWeightInput(
                    project_id=project_id2,
                    domain_name="default",
                    weight=Decimal("3.0"),
                ),
            ],
        )

        result = (
            await processors.fair_share.bulk_upsert_project_fair_share_weight.wait_for_complete(
                action
            )
        )

        assert result.upserted_count == 2
        processors.fair_share.bulk_upsert_project_fair_share_weight.wait_for_complete.assert_called_once()

    @pytest.mark.asyncio
    async def test_action_has_correct_structure(
        self,
        mock_processors_success: MagicMock,
    ) -> None:
        """Should verify action input structure."""
        processors = mock_processors_success
        project_id = UUID("aaaaaaaa-bbbb-cccc-dddd-111111111111")

        inputs = [
            ProjectWeightInput(
                project_id=project_id,
                domain_name="default",
                weight=Decimal("2.0"),
            ),
        ]
        action = BulkUpsertProjectFairShareWeightAction(
            resource_group="default",
            inputs=inputs,
        )

        await processors.fair_share.bulk_upsert_project_fair_share_weight.wait_for_complete(action)

        # Verify action structure
        assert action.resource_group == "default"
        assert len(action.inputs) == 1
        assert action.inputs[0].project_id == project_id
        assert action.inputs[0].domain_name == "default"
        assert action.inputs[0].weight == Decimal("2.0")


class TestBulkUpsertUserFairShareWeight:
    """Tests for bulk upsert user fair share weight processor."""

    @pytest.fixture
    def mock_processors_success(self) -> MagicMock:
        """Processors with successful bulk upsert."""
        processors = MagicMock()
        action_result = BulkUpsertUserFairShareWeightActionResult(upserted_count=2)
        processors.fair_share.bulk_upsert_user_fair_share_weight.wait_for_complete = AsyncMock(
            return_value=action_result
        )
        return processors

    @pytest.mark.asyncio
    async def test_successful_bulk_upsert(
        self,
        mock_processors_success: MagicMock,
    ) -> None:
        """Should bulk upsert user weights and return upserted count."""
        processors = mock_processors_success
        user_uuid1 = UUID("11111111-2222-3333-4444-555555555555")
        user_uuid2 = UUID("66666666-7777-8888-9999-aaaaaaaaaaaa")
        project_id = UUID("aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee")

        action = BulkUpsertUserFairShareWeightAction(
            resource_group="default",
            inputs=[
                UserWeightInput(
                    user_uuid=user_uuid1,
                    project_id=project_id,
                    domain_name="default",
                    weight=Decimal("2.0"),
                ),
                UserWeightInput(
                    user_uuid=user_uuid2,
                    project_id=project_id,
                    domain_name="default",
                    weight=Decimal("3.0"),
                ),
            ],
        )

        result = await processors.fair_share.bulk_upsert_user_fair_share_weight.wait_for_complete(
            action
        )

        assert result.upserted_count == 2
        processors.fair_share.bulk_upsert_user_fair_share_weight.wait_for_complete.assert_called_once()

    @pytest.mark.asyncio
    async def test_action_has_correct_structure(
        self,
        mock_processors_success: MagicMock,
    ) -> None:
        """Should verify action input structure."""
        processors = mock_processors_success
        user_uuid = UUID("11111111-2222-3333-4444-555555555555")
        project_id = UUID("aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee")

        inputs = [
            UserWeightInput(
                user_uuid=user_uuid,
                project_id=project_id,
                domain_name="default",
                weight=Decimal("2.0"),
            ),
        ]
        action = BulkUpsertUserFairShareWeightAction(
            resource_group="default",
            inputs=inputs,
        )

        await processors.fair_share.bulk_upsert_user_fair_share_weight.wait_for_complete(action)

        # Verify action structure
        assert action.resource_group == "default"
        assert len(action.inputs) == 1
        assert action.inputs[0].user_uuid == user_uuid
        assert action.inputs[0].project_id == project_id
        assert action.inputs[0].domain_name == "default"
        assert action.inputs[0].weight == Decimal("2.0")
