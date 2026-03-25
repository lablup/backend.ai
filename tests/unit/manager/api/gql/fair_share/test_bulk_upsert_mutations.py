"""Tests for bulk upsert fair share weight GQL mutations."""

from __future__ import annotations

import uuid
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest
from aiohttp import web

from ai.backend.common.dto.manager.v2.fair_share.response import (
    BulkUpsertDomainFairShareWeightPayload as BulkUpsertDomainFairShareWeightPayloadDTO,
)
from ai.backend.common.dto.manager.v2.fair_share.response import (
    BulkUpsertProjectFairShareWeightPayload as BulkUpsertProjectFairShareWeightPayloadDTO,
)
from ai.backend.common.dto.manager.v2.fair_share.response import (
    BulkUpsertUserFairShareWeightPayload as BulkUpsertUserFairShareWeightPayloadDTO,
)
from ai.backend.manager.api.gql.fair_share.resolver import domain as domain_resolver
from ai.backend.manager.api.gql.fair_share.resolver import project as project_resolver
from ai.backend.manager.api.gql.fair_share.resolver import user as user_resolver
from ai.backend.manager.api.gql.fair_share.types.domain import (
    BulkUpsertDomainFairShareWeightInput,
    DomainWeightInputItem,
)
from ai.backend.manager.api.gql.fair_share.types.project import (
    BulkUpsertProjectFairShareWeightInput,
    ProjectWeightInputItem,
)
from ai.backend.manager.api.gql.fair_share.types.user import (
    BulkUpsertUserFairShareWeightInput,
    UserWeightInputItem,
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


def create_mock_info_with_adapters(
    bulk_upsert_domain: AsyncMock | None = None,
    bulk_upsert_project: AsyncMock | None = None,
    bulk_upsert_user: AsyncMock | None = None,
) -> MagicMock:
    """Create mock strawberry.Info with adapter mocks."""
    info = MagicMock()
    if bulk_upsert_domain:
        info.context.adapters.fair_share.bulk_upsert_domain = bulk_upsert_domain
    if bulk_upsert_project:
        info.context.adapters.fair_share.bulk_upsert_project = bulk_upsert_project
    if bulk_upsert_user:
        info.context.adapters.fair_share.bulk_upsert_user = bulk_upsert_user
    return info


# Domain Bulk Upsert Mutation Tests


class TestBulkUpsertDomainFairShareWeightMutation:
    """Tests for bulk_upsert_domain_fair_share_weight mutation."""

    async def test_mutation_calls_adapter_with_correct_input(
        self,
        mock_superadmin_user: MagicMock,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test that mutation calls adapter with correct input parameters."""
        mock_adapter = AsyncMock(
            return_value=BulkUpsertDomainFairShareWeightPayloadDTO(upserted_count=2)
        )
        mock_info = create_mock_info_with_adapters(bulk_upsert_domain=mock_adapter)

        monkeypatch.setattr(
            domain_resolver,
            "current_user",
            lambda: mock_superadmin_user,
        )

        input_data = BulkUpsertDomainFairShareWeightInput(
            resource_group_name="default",
            inputs=[
                DomainWeightInputItem(domain_name="domain1", weight=Decimal("1.5")),
                DomainWeightInputItem(domain_name="domain2", weight=None),
            ],
        )

        resolver_fn = domain_resolver.bulk_upsert_domain_fair_share_weight.base_resolver
        result = await resolver_fn(mock_info, input_data)

        mock_adapter.assert_called_once()
        call_arg = mock_adapter.call_args[0][0]
        assert call_arg.resource_group_name == "default"
        assert len(call_arg.inputs) == 2
        assert call_arg.inputs[0].domain_name == "domain1"
        assert call_arg.inputs[0].weight == Decimal("1.5")
        assert call_arg.inputs[1].domain_name == "domain2"
        assert call_arg.inputs[1].weight is None

        assert result.upserted_count == 2

    async def test_mutation_returns_correct_count(
        self,
        mock_superadmin_user: MagicMock,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test that mutation returns correct upserted count."""
        mock_adapter = AsyncMock(
            return_value=BulkUpsertDomainFairShareWeightPayloadDTO(upserted_count=5)
        )
        mock_info = create_mock_info_with_adapters(bulk_upsert_domain=mock_adapter)

        monkeypatch.setattr(
            domain_resolver,
            "current_user",
            lambda: mock_superadmin_user,
        )

        input_data = BulkUpsertDomainFairShareWeightInput(
            resource_group_name="default",
            inputs=[
                DomainWeightInputItem(domain_name=f"domain{i}", weight=Decimal(str(i)))
                for i in range(5)
            ],
        )

        resolver_fn = domain_resolver.bulk_upsert_domain_fair_share_weight.base_resolver
        result = await resolver_fn(mock_info, input_data)

        assert result.upserted_count == 5

    async def test_mutation_requires_superadmin(
        self,
        mock_regular_user: MagicMock,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test that mutation requires superadmin privilege."""
        mock_adapter = AsyncMock()
        mock_info = create_mock_info_with_adapters(bulk_upsert_domain=mock_adapter)

        monkeypatch.setattr(
            domain_resolver,
            "current_user",
            lambda: mock_regular_user,
        )

        input_data = BulkUpsertDomainFairShareWeightInput(
            resource_group_name="default",
            inputs=[DomainWeightInputItem(domain_name="domain1", weight=Decimal("1.0"))],
        )

        resolver_fn = domain_resolver.bulk_upsert_domain_fair_share_weight.base_resolver
        with pytest.raises(web.HTTPForbidden):
            await resolver_fn(mock_info, input_data)

        mock_adapter.assert_not_called()


# Project Bulk Upsert Mutation Tests


class TestBulkUpsertProjectFairShareWeightMutation:
    """Tests for bulk_upsert_project_fair_share_weight mutation."""

    async def test_mutation_calls_adapter_with_correct_input(
        self,
        mock_superadmin_user: MagicMock,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test that mutation calls adapter with correct input parameters."""
        project_id1 = uuid.uuid4()
        project_id2 = uuid.uuid4()
        mock_adapter = AsyncMock(
            return_value=BulkUpsertProjectFairShareWeightPayloadDTO(upserted_count=2)
        )
        mock_info = create_mock_info_with_adapters(bulk_upsert_project=mock_adapter)

        monkeypatch.setattr(
            project_resolver,
            "current_user",
            lambda: mock_superadmin_user,
        )

        input_data = BulkUpsertProjectFairShareWeightInput(
            resource_group_name="default",
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

        resolver_fn = project_resolver.bulk_upsert_project_fair_share_weight.base_resolver
        result = await resolver_fn(mock_info, input_data)

        mock_adapter.assert_called_once()
        call_arg = mock_adapter.call_args[0][0]
        assert call_arg.resource_group_name == "default"
        assert len(call_arg.inputs) == 2
        assert call_arg.inputs[0].project_id == project_id1
        assert call_arg.inputs[0].domain_name == "domain1"
        assert call_arg.inputs[0].weight == Decimal("1.5")
        assert call_arg.inputs[1].project_id == project_id2
        assert call_arg.inputs[1].domain_name == "domain2"
        assert call_arg.inputs[1].weight is None

        assert result.upserted_count == 2

    async def test_mutation_requires_superadmin(
        self,
        mock_regular_user: MagicMock,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test that mutation requires superadmin privilege."""
        mock_adapter = AsyncMock()
        mock_info = create_mock_info_with_adapters(bulk_upsert_project=mock_adapter)

        monkeypatch.setattr(
            project_resolver,
            "current_user",
            lambda: mock_regular_user,
        )

        input_data = BulkUpsertProjectFairShareWeightInput(
            resource_group_name="default",
            inputs=[
                ProjectWeightInputItem(
                    project_id=uuid.uuid4(),
                    domain_name="domain1",
                    weight=Decimal("1.0"),
                )
            ],
        )

        resolver_fn = project_resolver.bulk_upsert_project_fair_share_weight.base_resolver
        with pytest.raises(web.HTTPForbidden):
            await resolver_fn(mock_info, input_data)

        mock_adapter.assert_not_called()


# User Bulk Upsert Mutation Tests


class TestBulkUpsertUserFairShareWeightMutation:
    """Tests for bulk_upsert_user_fair_share_weight mutation."""

    async def test_mutation_calls_adapter_with_correct_input(
        self,
        mock_superadmin_user: MagicMock,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test that mutation calls adapter with correct input parameters."""
        user_uuid1 = uuid.uuid4()
        user_uuid2 = uuid.uuid4()
        project_id1 = uuid.uuid4()
        project_id2 = uuid.uuid4()
        mock_adapter = AsyncMock(
            return_value=BulkUpsertUserFairShareWeightPayloadDTO(upserted_count=2)
        )
        mock_info = create_mock_info_with_adapters(bulk_upsert_user=mock_adapter)

        monkeypatch.setattr(
            user_resolver,
            "current_user",
            lambda: mock_superadmin_user,
        )

        input_data = BulkUpsertUserFairShareWeightInput(
            resource_group_name="default",
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

        resolver_fn = user_resolver.bulk_upsert_user_fair_share_weight.base_resolver
        result = await resolver_fn(mock_info, input_data)

        mock_adapter.assert_called_once()
        call_arg = mock_adapter.call_args[0][0]
        assert call_arg.resource_group_name == "default"
        assert len(call_arg.inputs) == 2
        assert call_arg.inputs[0].user_uuid == user_uuid1
        assert call_arg.inputs[0].project_id == project_id1
        assert call_arg.inputs[0].domain_name == "domain1"
        assert call_arg.inputs[0].weight == Decimal("1.5")
        assert call_arg.inputs[1].user_uuid == user_uuid2
        assert call_arg.inputs[1].project_id == project_id2
        assert call_arg.inputs[1].domain_name == "domain2"
        assert call_arg.inputs[1].weight is None

        assert result.upserted_count == 2

    async def test_mutation_requires_superadmin(
        self,
        mock_regular_user: MagicMock,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test that mutation requires superadmin privilege."""
        mock_adapter = AsyncMock()
        mock_info = create_mock_info_with_adapters(bulk_upsert_user=mock_adapter)

        monkeypatch.setattr(
            user_resolver,
            "current_user",
            lambda: mock_regular_user,
        )

        input_data = BulkUpsertUserFairShareWeightInput(
            resource_group_name="default",
            inputs=[
                UserWeightInputItem(
                    user_uuid=uuid.uuid4(),
                    project_id=uuid.uuid4(),
                    domain_name="domain1",
                    weight=Decimal("1.0"),
                )
            ],
        )

        resolver_fn = user_resolver.bulk_upsert_user_fair_share_weight.base_resolver
        with pytest.raises(web.HTTPForbidden):
            await resolver_fn(mock_info, input_data)

        mock_adapter.assert_not_called()
