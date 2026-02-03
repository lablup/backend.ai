"""Tests for bulk upsert fair share weight GQL mutations."""

from __future__ import annotations

import uuid
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest
from aiohttp import web

from ai.backend.manager.api.gql.fair_share.resolver import domain as domain_resolver
from ai.backend.manager.api.gql.fair_share.resolver import project as project_resolver
from ai.backend.manager.api.gql.fair_share.resolver import user as user_resolver
from ai.backend.manager.api.gql.fair_share.types.domain import (
    BulkUpsertDomainFairShareWeightInput,
    BulkUpsertDomainFairShareWeightPayload,
    DomainWeightInputItem,
)
from ai.backend.manager.api.gql.fair_share.types.project import (
    BulkUpsertProjectFairShareWeightInput,
    BulkUpsertProjectFairShareWeightPayload,
    ProjectWeightInputItem,
)
from ai.backend.manager.api.gql.fair_share.types.user import (
    BulkUpsertUserFairShareWeightInput,
    BulkUpsertUserFairShareWeightPayload,
    UserWeightInputItem,
)
from ai.backend.manager.services.fair_share.actions import (
    BulkUpsertDomainFairShareWeightActionResult,
    BulkUpsertProjectFairShareWeightActionResult,
    BulkUpsertUserFairShareWeightActionResult,
)

# Common fixtures


@pytest.fixture
def mock_superadmin_user() -> MagicMock:
    """Create mock superadmin user."""
    user = MagicMock()
    user.is_superadmin = True
    return user


@pytest.fixture
def mock_regular_user() -> MagicMock:
    """Create mock regular (non-superadmin) user."""
    user = MagicMock()
    user.is_superadmin = False
    return user


@pytest.fixture
def mock_bulk_upsert_domain_processor() -> AsyncMock:
    """Create mock bulk_upsert_domain_fair_share_weight processor."""
    return AsyncMock()


@pytest.fixture
def mock_bulk_upsert_project_processor() -> AsyncMock:
    """Create mock bulk_upsert_project_fair_share_weight processor."""
    return AsyncMock()


@pytest.fixture
def mock_bulk_upsert_user_processor() -> AsyncMock:
    """Create mock bulk_upsert_user_fair_share_weight processor."""
    return AsyncMock()


def create_mock_context(
    domain_processor: AsyncMock | None = None,
    project_processor: AsyncMock | None = None,
    user_processor: AsyncMock | None = None,
) -> MagicMock:
    """Create mock GraphQL context with processors."""
    context = MagicMock()
    context.processors = MagicMock()
    context.processors.fair_share = MagicMock()

    if domain_processor:
        context.processors.fair_share.bulk_upsert_domain_fair_share_weight = domain_processor
    if project_processor:
        context.processors.fair_share.bulk_upsert_project_fair_share_weight = project_processor
    if user_processor:
        context.processors.fair_share.bulk_upsert_user_fair_share_weight = user_processor

    return context


def create_mock_info(context: MagicMock) -> MagicMock:
    """Create mock strawberry.Info with context."""
    info = MagicMock()
    info.context = context
    return info


# Domain Bulk Upsert Mutation Tests


class TestBulkUpsertDomainFairShareWeightMutation:
    """Tests for bulk_upsert_domain_fair_share_weight mutation."""

    @pytest.mark.asyncio
    async def test_mutation_calls_processor_with_correct_action(
        self,
        mock_superadmin_user: MagicMock,
        mock_bulk_upsert_domain_processor: AsyncMock,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test that mutation calls processor with correct action parameters."""
        # Given
        mock_bulk_upsert_domain_processor.wait_for_complete.return_value = (
            BulkUpsertDomainFairShareWeightActionResult(upserted_count=2)
        )
        context = create_mock_context(domain_processor=mock_bulk_upsert_domain_processor)
        mock_info = create_mock_info(context)

        monkeypatch.setattr(
            domain_resolver,
            "current_user",
            lambda: mock_superadmin_user,
        )

        input_data = BulkUpsertDomainFairShareWeightInput(
            resource_group="default",
            inputs=[
                DomainWeightInputItem(domain_name="domain1", weight=Decimal("1.5")),
                DomainWeightInputItem(domain_name="domain2", weight=None),
            ],
        )

        # When - access the underlying resolver function
        resolver_fn = domain_resolver.bulk_upsert_domain_fair_share_weight.base_resolver
        result = await resolver_fn(mock_info, input_data)

        # Then
        mock_bulk_upsert_domain_processor.wait_for_complete.assert_called_once()
        call_args = mock_bulk_upsert_domain_processor.wait_for_complete.call_args
        action = call_args[0][0]

        assert action.resource_group == "default"
        assert len(action.inputs) == 2
        assert action.inputs[0].domain_name == "domain1"
        assert action.inputs[0].weight == Decimal("1.5")
        assert action.inputs[1].domain_name == "domain2"
        assert action.inputs[1].weight is None

        assert isinstance(result, BulkUpsertDomainFairShareWeightPayload)
        assert result.upserted_count == 2

    @pytest.mark.asyncio
    async def test_mutation_returns_correct_count(
        self,
        mock_superadmin_user: MagicMock,
        mock_bulk_upsert_domain_processor: AsyncMock,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test that mutation returns correct upserted count."""
        # Given
        mock_bulk_upsert_domain_processor.wait_for_complete.return_value = (
            BulkUpsertDomainFairShareWeightActionResult(upserted_count=5)
        )
        context = create_mock_context(domain_processor=mock_bulk_upsert_domain_processor)
        mock_info = create_mock_info(context)

        monkeypatch.setattr(
            domain_resolver,
            "current_user",
            lambda: mock_superadmin_user,
        )

        input_data = BulkUpsertDomainFairShareWeightInput(
            resource_group="default",
            inputs=[
                DomainWeightInputItem(domain_name=f"domain{i}", weight=Decimal(str(i)))
                for i in range(5)
            ],
        )

        # When - access the underlying resolver function
        resolver_fn = domain_resolver.bulk_upsert_domain_fair_share_weight.base_resolver
        result = await resolver_fn(mock_info, input_data)

        # Then
        assert result.upserted_count == 5

    @pytest.mark.asyncio
    async def test_mutation_requires_superadmin(
        self,
        mock_regular_user: MagicMock,
        mock_bulk_upsert_domain_processor: AsyncMock,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test that mutation requires superadmin privilege."""
        # Given
        context = create_mock_context(domain_processor=mock_bulk_upsert_domain_processor)
        mock_info = create_mock_info(context)

        monkeypatch.setattr(
            domain_resolver,
            "current_user",
            lambda: mock_regular_user,
        )

        input_data = BulkUpsertDomainFairShareWeightInput(
            resource_group="default",
            inputs=[DomainWeightInputItem(domain_name="domain1", weight=Decimal("1.0"))],
        )

        # When / Then - access the underlying resolver function
        resolver_fn = domain_resolver.bulk_upsert_domain_fair_share_weight.base_resolver
        with pytest.raises(web.HTTPForbidden):
            await resolver_fn(mock_info, input_data)

        mock_bulk_upsert_domain_processor.wait_for_complete.assert_not_called()


# Project Bulk Upsert Mutation Tests


class TestBulkUpsertProjectFairShareWeightMutation:
    """Tests for bulk_upsert_project_fair_share_weight mutation."""

    @pytest.mark.asyncio
    async def test_mutation_calls_processor_with_correct_action(
        self,
        mock_superadmin_user: MagicMock,
        mock_bulk_upsert_project_processor: AsyncMock,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test that mutation calls processor with correct action parameters."""
        # Given
        project_id1 = uuid.uuid4()
        project_id2 = uuid.uuid4()
        mock_bulk_upsert_project_processor.wait_for_complete.return_value = (
            BulkUpsertProjectFairShareWeightActionResult(upserted_count=2)
        )
        context = create_mock_context(project_processor=mock_bulk_upsert_project_processor)
        mock_info = create_mock_info(context)

        monkeypatch.setattr(
            project_resolver,
            "current_user",
            lambda: mock_superadmin_user,
        )

        input_data = BulkUpsertProjectFairShareWeightInput(
            resource_group="default",
            inputs=[
                ProjectWeightInputItem(
                    project_id=project_id1,
                    domain_name="domain1",
                    weight=Decimal("1.5"),
                ),
                ProjectWeightInputItem(
                    project_id=project_id2,
                    domain_name="domain2",
                    weight=None,
                ),
            ],
        )

        # When - access the underlying resolver function
        resolver_fn = project_resolver.bulk_upsert_project_fair_share_weight.base_resolver
        result = await resolver_fn(mock_info, input_data)

        # Then
        mock_bulk_upsert_project_processor.wait_for_complete.assert_called_once()
        call_args = mock_bulk_upsert_project_processor.wait_for_complete.call_args
        action = call_args[0][0]

        assert action.resource_group == "default"
        assert len(action.inputs) == 2
        assert action.inputs[0].project_id == project_id1
        assert action.inputs[0].domain_name == "domain1"
        assert action.inputs[0].weight == Decimal("1.5")
        assert action.inputs[1].project_id == project_id2
        assert action.inputs[1].domain_name == "domain2"
        assert action.inputs[1].weight is None

        assert isinstance(result, BulkUpsertProjectFairShareWeightPayload)
        assert result.upserted_count == 2

    @pytest.mark.asyncio
    async def test_mutation_requires_superadmin(
        self,
        mock_regular_user: MagicMock,
        mock_bulk_upsert_project_processor: AsyncMock,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test that mutation requires superadmin privilege."""
        # Given
        context = create_mock_context(project_processor=mock_bulk_upsert_project_processor)
        mock_info = create_mock_info(context)

        monkeypatch.setattr(
            project_resolver,
            "current_user",
            lambda: mock_regular_user,
        )

        input_data = BulkUpsertProjectFairShareWeightInput(
            resource_group="default",
            inputs=[
                ProjectWeightInputItem(
                    project_id=uuid.uuid4(),
                    domain_name="domain1",
                    weight=Decimal("1.0"),
                )
            ],
        )

        # When / Then - access the underlying resolver function
        resolver_fn = project_resolver.bulk_upsert_project_fair_share_weight.base_resolver
        with pytest.raises(web.HTTPForbidden):
            await resolver_fn(mock_info, input_data)

        mock_bulk_upsert_project_processor.wait_for_complete.assert_not_called()


# User Bulk Upsert Mutation Tests


class TestBulkUpsertUserFairShareWeightMutation:
    """Tests for bulk_upsert_user_fair_share_weight mutation."""

    @pytest.mark.asyncio
    async def test_mutation_calls_processor_with_correct_action(
        self,
        mock_superadmin_user: MagicMock,
        mock_bulk_upsert_user_processor: AsyncMock,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test that mutation calls processor with correct action parameters."""
        # Given
        user_uuid1 = uuid.uuid4()
        user_uuid2 = uuid.uuid4()
        project_id1 = uuid.uuid4()
        project_id2 = uuid.uuid4()
        mock_bulk_upsert_user_processor.wait_for_complete.return_value = (
            BulkUpsertUserFairShareWeightActionResult(upserted_count=2)
        )
        context = create_mock_context(user_processor=mock_bulk_upsert_user_processor)
        mock_info = create_mock_info(context)

        monkeypatch.setattr(
            user_resolver,
            "current_user",
            lambda: mock_superadmin_user,
        )

        input_data = BulkUpsertUserFairShareWeightInput(
            resource_group="default",
            inputs=[
                UserWeightInputItem(
                    user_uuid=user_uuid1,
                    project_id=project_id1,
                    domain_name="domain1",
                    weight=Decimal("1.5"),
                ),
                UserWeightInputItem(
                    user_uuid=user_uuid2,
                    project_id=project_id2,
                    domain_name="domain2",
                    weight=None,
                ),
            ],
        )

        # When - access the underlying resolver function
        resolver_fn = user_resolver.bulk_upsert_user_fair_share_weight.base_resolver
        result = await resolver_fn(mock_info, input_data)

        # Then
        mock_bulk_upsert_user_processor.wait_for_complete.assert_called_once()
        call_args = mock_bulk_upsert_user_processor.wait_for_complete.call_args
        action = call_args[0][0]

        assert action.resource_group == "default"
        assert len(action.inputs) == 2
        assert action.inputs[0].user_uuid == user_uuid1
        assert action.inputs[0].project_id == project_id1
        assert action.inputs[0].domain_name == "domain1"
        assert action.inputs[0].weight == Decimal("1.5")
        assert action.inputs[1].user_uuid == user_uuid2
        assert action.inputs[1].project_id == project_id2
        assert action.inputs[1].domain_name == "domain2"
        assert action.inputs[1].weight is None

        assert isinstance(result, BulkUpsertUserFairShareWeightPayload)
        assert result.upserted_count == 2

    @pytest.mark.asyncio
    async def test_mutation_requires_superadmin(
        self,
        mock_regular_user: MagicMock,
        mock_bulk_upsert_user_processor: AsyncMock,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test that mutation requires superadmin privilege."""
        # Given
        context = create_mock_context(user_processor=mock_bulk_upsert_user_processor)
        mock_info = create_mock_info(context)

        monkeypatch.setattr(
            user_resolver,
            "current_user",
            lambda: mock_regular_user,
        )

        input_data = BulkUpsertUserFairShareWeightInput(
            resource_group="default",
            inputs=[
                UserWeightInputItem(
                    user_uuid=uuid.uuid4(),
                    project_id=uuid.uuid4(),
                    domain_name="domain1",
                    weight=Decimal("1.0"),
                )
            ],
        )

        # When / Then - access the underlying resolver function
        resolver_fn = user_resolver.bulk_upsert_user_fair_share_weight.base_resolver
        with pytest.raises(web.HTTPForbidden):
            await resolver_fn(mock_info, input_data)

        mock_bulk_upsert_user_processor.wait_for_complete.assert_not_called()
