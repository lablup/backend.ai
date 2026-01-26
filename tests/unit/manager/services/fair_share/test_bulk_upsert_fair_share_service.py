"""Tests for FairShareService bulk upsert operations."""

from __future__ import annotations

import uuid
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.manager.repositories.base import BulkUpserterResult
from ai.backend.manager.repositories.fair_share import (
    DomainFairShareBulkWeightUpserterSpec,
    FairShareRepository,
    ProjectFairShareBulkWeightUpserterSpec,
    UserFairShareBulkWeightUpserterSpec,
)
from ai.backend.manager.services.fair_share import FairShareService
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


@pytest.fixture
def mock_repository() -> MagicMock:
    return MagicMock(spec=FairShareRepository)


@pytest.fixture
def service(mock_repository: MagicMock) -> FairShareService:
    return FairShareService(repository=mock_repository)


# Domain Bulk Upsert Tests


class TestBulkUpsertDomainFairShareWeight:
    """Tests for bulk upsert domain fair share weight."""

    @pytest.mark.asyncio
    async def test_bulk_upsert_single_domain_calls_repository(
        self,
        service: FairShareService,
        mock_repository: MagicMock,
    ) -> None:
        """Should call repository with single item bulk upserter."""
        mock_repository.bulk_upsert_domain_fair_share = AsyncMock(
            return_value=BulkUpserterResult(upserted_count=1)
        )

        action = BulkUpsertDomainFairShareWeightAction(
            resource_group="default",
            inputs=[
                DomainWeightInput(domain_name="domain1", weight=Decimal("1.5")),
            ],
        )

        result = await service.bulk_upsert_domain_fair_share_weight(action)

        mock_repository.bulk_upsert_domain_fair_share.assert_called_once()
        assert result.upserted_count == 1
        assert isinstance(result, BulkUpsertDomainFairShareWeightActionResult)

    @pytest.mark.asyncio
    async def test_bulk_upsert_multiple_domains_calls_repository(
        self,
        service: FairShareService,
        mock_repository: MagicMock,
    ) -> None:
        """Should call repository with multiple item bulk upserter."""
        mock_repository.bulk_upsert_domain_fair_share = AsyncMock(
            return_value=BulkUpserterResult(upserted_count=3)
        )

        action = BulkUpsertDomainFairShareWeightAction(
            resource_group="default",
            inputs=[
                DomainWeightInput(domain_name="domain1", weight=Decimal("1.0")),
                DomainWeightInput(domain_name="domain2", weight=Decimal("2.0")),
                DomainWeightInput(domain_name="domain3", weight=None),  # Use default
            ],
        )

        result = await service.bulk_upsert_domain_fair_share_weight(action)

        mock_repository.bulk_upsert_domain_fair_share.assert_called_once()
        assert result.upserted_count == 3

    @pytest.mark.asyncio
    async def test_bulk_upsert_creates_correct_specs(
        self,
        service: FairShareService,
        mock_repository: MagicMock,
    ) -> None:
        """Should create correct upserter specs for each input."""
        mock_repository.bulk_upsert_domain_fair_share = AsyncMock(
            return_value=BulkUpserterResult(upserted_count=2)
        )

        action = BulkUpsertDomainFairShareWeightAction(
            resource_group="test-rg",
            inputs=[
                DomainWeightInput(domain_name="domain1", weight=Decimal("1.5")),
                DomainWeightInput(domain_name="domain2", weight=None),
            ],
        )

        await service.bulk_upsert_domain_fair_share_weight(action)

        call_args = mock_repository.bulk_upsert_domain_fair_share.call_args
        bulk_upserter = call_args[0][0]

        # Verify specs were created correctly
        specs = bulk_upserter.specs
        assert len(specs) == 2
        assert all(isinstance(s, DomainFairShareBulkWeightUpserterSpec) for s in specs)
        assert specs[0].resource_group == "test-rg"
        assert specs[0].domain_name == "domain1"
        assert specs[0].weight == Decimal("1.5")
        assert specs[1].resource_group == "test-rg"
        assert specs[1].domain_name == "domain2"
        assert specs[1].weight is None

    @pytest.mark.asyncio
    async def test_bulk_upsert_empty_inputs_returns_zero(
        self,
        service: FairShareService,
        mock_repository: MagicMock,
    ) -> None:
        """Should return zero count for empty inputs without calling repository."""
        action = BulkUpsertDomainFairShareWeightAction(
            resource_group="default",
            inputs=[],
        )

        result = await service.bulk_upsert_domain_fair_share_weight(action)

        mock_repository.bulk_upsert_domain_fair_share.assert_not_called()
        assert result.upserted_count == 0


# Project Bulk Upsert Tests


class TestBulkUpsertProjectFairShareWeight:
    """Tests for bulk upsert project fair share weight."""

    @pytest.mark.asyncio
    async def test_bulk_upsert_single_project_calls_repository(
        self,
        service: FairShareService,
        mock_repository: MagicMock,
    ) -> None:
        """Should call repository with single item bulk upserter."""
        project_id = uuid.uuid4()
        mock_repository.bulk_upsert_project_fair_share = AsyncMock(
            return_value=BulkUpserterResult(upserted_count=1)
        )

        action = BulkUpsertProjectFairShareWeightAction(
            resource_group="default",
            inputs=[
                ProjectWeightInput(
                    project_id=project_id,
                    domain_name="domain1",
                    weight=Decimal("1.5"),
                ),
            ],
        )

        result = await service.bulk_upsert_project_fair_share_weight(action)

        mock_repository.bulk_upsert_project_fair_share.assert_called_once()
        assert result.upserted_count == 1
        assert isinstance(result, BulkUpsertProjectFairShareWeightActionResult)

    @pytest.mark.asyncio
    async def test_bulk_upsert_multiple_projects_calls_repository(
        self,
        service: FairShareService,
        mock_repository: MagicMock,
    ) -> None:
        """Should call repository with multiple item bulk upserter."""
        project_ids = [uuid.uuid4() for _ in range(3)]
        mock_repository.bulk_upsert_project_fair_share = AsyncMock(
            return_value=BulkUpserterResult(upserted_count=3)
        )

        action = BulkUpsertProjectFairShareWeightAction(
            resource_group="default",
            inputs=[
                ProjectWeightInput(
                    project_id=project_ids[0],
                    domain_name="domain1",
                    weight=Decimal("1.0"),
                ),
                ProjectWeightInput(
                    project_id=project_ids[1],
                    domain_name="domain1",
                    weight=Decimal("2.0"),
                ),
                ProjectWeightInput(
                    project_id=project_ids[2],
                    domain_name="domain2",
                    weight=None,
                ),
            ],
        )

        result = await service.bulk_upsert_project_fair_share_weight(action)

        mock_repository.bulk_upsert_project_fair_share.assert_called_once()
        assert result.upserted_count == 3

    @pytest.mark.asyncio
    async def test_bulk_upsert_creates_correct_specs(
        self,
        service: FairShareService,
        mock_repository: MagicMock,
    ) -> None:
        """Should create correct upserter specs for each input."""
        project_id1 = uuid.uuid4()
        project_id2 = uuid.uuid4()
        mock_repository.bulk_upsert_project_fair_share = AsyncMock(
            return_value=BulkUpserterResult(upserted_count=2)
        )

        action = BulkUpsertProjectFairShareWeightAction(
            resource_group="test-rg",
            inputs=[
                ProjectWeightInput(
                    project_id=project_id1,
                    domain_name="domain1",
                    weight=Decimal("1.5"),
                ),
                ProjectWeightInput(
                    project_id=project_id2,
                    domain_name="domain2",
                    weight=None,
                ),
            ],
        )

        await service.bulk_upsert_project_fair_share_weight(action)

        call_args = mock_repository.bulk_upsert_project_fair_share.call_args
        bulk_upserter = call_args[0][0]

        specs = bulk_upserter.specs
        assert len(specs) == 2
        assert all(isinstance(s, ProjectFairShareBulkWeightUpserterSpec) for s in specs)
        assert specs[0].resource_group == "test-rg"
        assert specs[0].project_id == project_id1
        assert specs[0].domain_name == "domain1"
        assert specs[0].weight == Decimal("1.5")
        assert specs[1].resource_group == "test-rg"
        assert specs[1].project_id == project_id2
        assert specs[1].domain_name == "domain2"
        assert specs[1].weight is None

    @pytest.mark.asyncio
    async def test_bulk_upsert_empty_inputs_returns_zero(
        self,
        service: FairShareService,
        mock_repository: MagicMock,
    ) -> None:
        """Should return zero count for empty inputs without calling repository."""
        action = BulkUpsertProjectFairShareWeightAction(
            resource_group="default",
            inputs=[],
        )

        result = await service.bulk_upsert_project_fair_share_weight(action)

        mock_repository.bulk_upsert_project_fair_share.assert_not_called()
        assert result.upserted_count == 0


# User Bulk Upsert Tests


class TestBulkUpsertUserFairShareWeight:
    """Tests for bulk upsert user fair share weight."""

    @pytest.mark.asyncio
    async def test_bulk_upsert_single_user_calls_repository(
        self,
        service: FairShareService,
        mock_repository: MagicMock,
    ) -> None:
        """Should call repository with single item bulk upserter."""
        user_uuid = uuid.uuid4()
        project_id = uuid.uuid4()
        mock_repository.bulk_upsert_user_fair_share = AsyncMock(
            return_value=BulkUpserterResult(upserted_count=1)
        )

        action = BulkUpsertUserFairShareWeightAction(
            resource_group="default",
            inputs=[
                UserWeightInput(
                    user_uuid=user_uuid,
                    project_id=project_id,
                    domain_name="domain1",
                    weight=Decimal("1.5"),
                ),
            ],
        )

        result = await service.bulk_upsert_user_fair_share_weight(action)

        mock_repository.bulk_upsert_user_fair_share.assert_called_once()
        assert result.upserted_count == 1
        assert isinstance(result, BulkUpsertUserFairShareWeightActionResult)

    @pytest.mark.asyncio
    async def test_bulk_upsert_multiple_users_calls_repository(
        self,
        service: FairShareService,
        mock_repository: MagicMock,
    ) -> None:
        """Should call repository with multiple item bulk upserter."""
        user_uuids = [uuid.uuid4() for _ in range(3)]
        project_ids = [uuid.uuid4() for _ in range(2)]
        mock_repository.bulk_upsert_user_fair_share = AsyncMock(
            return_value=BulkUpserterResult(upserted_count=3)
        )

        action = BulkUpsertUserFairShareWeightAction(
            resource_group="default",
            inputs=[
                UserWeightInput(
                    user_uuid=user_uuids[0],
                    project_id=project_ids[0],
                    domain_name="domain1",
                    weight=Decimal("1.0"),
                ),
                UserWeightInput(
                    user_uuid=user_uuids[1],
                    project_id=project_ids[0],
                    domain_name="domain1",
                    weight=Decimal("2.0"),
                ),
                UserWeightInput(
                    user_uuid=user_uuids[2],
                    project_id=project_ids[1],
                    domain_name="domain2",
                    weight=None,
                ),
            ],
        )

        result = await service.bulk_upsert_user_fair_share_weight(action)

        mock_repository.bulk_upsert_user_fair_share.assert_called_once()
        assert result.upserted_count == 3

    @pytest.mark.asyncio
    async def test_bulk_upsert_creates_correct_specs(
        self,
        service: FairShareService,
        mock_repository: MagicMock,
    ) -> None:
        """Should create correct upserter specs for each input."""
        user_uuid1 = uuid.uuid4()
        user_uuid2 = uuid.uuid4()
        project_id1 = uuid.uuid4()
        project_id2 = uuid.uuid4()
        mock_repository.bulk_upsert_user_fair_share = AsyncMock(
            return_value=BulkUpserterResult(upserted_count=2)
        )

        action = BulkUpsertUserFairShareWeightAction(
            resource_group="test-rg",
            inputs=[
                UserWeightInput(
                    user_uuid=user_uuid1,
                    project_id=project_id1,
                    domain_name="domain1",
                    weight=Decimal("1.5"),
                ),
                UserWeightInput(
                    user_uuid=user_uuid2,
                    project_id=project_id2,
                    domain_name="domain2",
                    weight=None,
                ),
            ],
        )

        await service.bulk_upsert_user_fair_share_weight(action)

        call_args = mock_repository.bulk_upsert_user_fair_share.call_args
        bulk_upserter = call_args[0][0]

        specs = bulk_upserter.specs
        assert len(specs) == 2
        assert all(isinstance(s, UserFairShareBulkWeightUpserterSpec) for s in specs)
        assert specs[0].resource_group == "test-rg"
        assert specs[0].user_uuid == user_uuid1
        assert specs[0].project_id == project_id1
        assert specs[0].domain_name == "domain1"
        assert specs[0].weight == Decimal("1.5")
        assert specs[1].resource_group == "test-rg"
        assert specs[1].user_uuid == user_uuid2
        assert specs[1].project_id == project_id2
        assert specs[1].domain_name == "domain2"
        assert specs[1].weight is None

    @pytest.mark.asyncio
    async def test_bulk_upsert_empty_inputs_returns_zero(
        self,
        service: FairShareService,
        mock_repository: MagicMock,
    ) -> None:
        """Should return zero count for empty inputs without calling repository."""
        action = BulkUpsertUserFairShareWeightAction(
            resource_group="default",
            inputs=[],
        )

        result = await service.bulk_upsert_user_fair_share_weight(action)

        mock_repository.bulk_upsert_user_fair_share.assert_not_called()
        assert result.upserted_count == 0
