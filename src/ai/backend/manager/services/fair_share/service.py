"""Fair Share Service."""

from __future__ import annotations

from ai.backend.manager.repositories.base import BatchQuerier, Upserter
from ai.backend.manager.repositories.fair_share import FairShareRepository
from ai.backend.manager.repositories.fair_share.upserters import (
    DomainFairShareUpserterSpec,
    ProjectFairShareUpserterSpec,
    UserFairShareUpserterSpec,
)
from ai.backend.manager.types import TriState

from .actions import (
    GetDomainFairShareAction,
    GetDomainFairShareActionResult,
    GetProjectFairShareAction,
    GetProjectFairShareActionResult,
    GetUserFairShareAction,
    GetUserFairShareActionResult,
    SearchDomainFairSharesAction,
    SearchDomainFairSharesActionResult,
    SearchProjectFairSharesAction,
    SearchProjectFairSharesActionResult,
    SearchUserFairSharesAction,
    SearchUserFairSharesActionResult,
    UpsertDomainFairShareWeightAction,
    UpsertDomainFairShareWeightActionResult,
    UpsertProjectFairShareWeightAction,
    UpsertProjectFairShareWeightActionResult,
    UpsertUserFairShareWeightAction,
    UpsertUserFairShareWeightActionResult,
)

__all__ = ("FairShareService",)


class FairShareService:
    """Service for fair share data operations.

    Provides read operations wrapping the FairShareRepository.
    Write operations (upsert) are handled directly by sokovan using the repository.
    """

    _repository: FairShareRepository

    def __init__(self, repository: FairShareRepository) -> None:
        self._repository = repository

    # Domain Fair Share

    async def get_domain_fair_share(
        self, action: GetDomainFairShareAction
    ) -> GetDomainFairShareActionResult:
        """Get a domain fair share record."""
        result = await self._repository.get_domain_fair_share(
            resource_group=action.resource_group,
            domain_name=action.domain_name,
        )
        return GetDomainFairShareActionResult(data=result)

    async def search_domain_fair_shares(
        self, action: SearchDomainFairSharesAction
    ) -> SearchDomainFairSharesActionResult:
        """Search domain fair shares with pagination."""
        querier = BatchQuerier(
            pagination=action.pagination,
            conditions=action.conditions,
            orders=action.orders,
        )
        result = await self._repository.search_domain_fair_shares(querier)
        return SearchDomainFairSharesActionResult(
            items=result.items,
            total_count=result.total_count,
        )

    # Project Fair Share

    async def get_project_fair_share(
        self, action: GetProjectFairShareAction
    ) -> GetProjectFairShareActionResult:
        """Get a project fair share record."""
        result = await self._repository.get_project_fair_share(
            resource_group=action.resource_group,
            project_id=action.project_id,
        )
        return GetProjectFairShareActionResult(data=result)

    async def search_project_fair_shares(
        self, action: SearchProjectFairSharesAction
    ) -> SearchProjectFairSharesActionResult:
        """Search project fair shares with pagination."""
        querier = BatchQuerier(
            pagination=action.pagination,
            conditions=action.conditions,
            orders=action.orders,
        )
        result = await self._repository.search_project_fair_shares(querier)
        return SearchProjectFairSharesActionResult(
            items=result.items,
            total_count=result.total_count,
        )

    # User Fair Share

    async def get_user_fair_share(
        self, action: GetUserFairShareAction
    ) -> GetUserFairShareActionResult:
        """Get a user fair share record."""
        result = await self._repository.get_user_fair_share(
            resource_group=action.resource_group,
            project_id=action.project_id,
            user_uuid=action.user_uuid,
        )
        return GetUserFairShareActionResult(data=result)

    async def search_user_fair_shares(
        self, action: SearchUserFairSharesAction
    ) -> SearchUserFairSharesActionResult:
        """Search user fair shares with pagination."""
        querier = BatchQuerier(
            pagination=action.pagination,
            conditions=action.conditions,
            orders=action.orders,
        )
        result = await self._repository.search_user_fair_shares(querier)
        return SearchUserFairSharesActionResult(
            items=result.items,
            total_count=result.total_count,
        )

    # Upsert Weight Operations

    async def upsert_domain_fair_share_weight(
        self, action: UpsertDomainFairShareWeightAction
    ) -> UpsertDomainFairShareWeightActionResult:
        """Upsert a domain fair share weight."""
        spec = DomainFairShareUpserterSpec(
            resource_group=action.resource_group,
            domain_name=action.domain_name,
            weight=TriState.from_graphql(action.weight),
        )
        upserter = Upserter(spec=spec)
        result = await self._repository.upsert_domain_fair_share(upserter)
        return UpsertDomainFairShareWeightActionResult(data=result)

    async def upsert_project_fair_share_weight(
        self, action: UpsertProjectFairShareWeightAction
    ) -> UpsertProjectFairShareWeightActionResult:
        """Upsert a project fair share weight."""
        spec = ProjectFairShareUpserterSpec(
            resource_group=action.resource_group,
            project_id=action.project_id,
            domain_name=action.domain_name,
            weight=TriState.from_graphql(action.weight),
        )
        upserter = Upserter(spec=spec)
        result = await self._repository.upsert_project_fair_share(upserter)
        return UpsertProjectFairShareWeightActionResult(data=result)

    async def upsert_user_fair_share_weight(
        self, action: UpsertUserFairShareWeightAction
    ) -> UpsertUserFairShareWeightActionResult:
        """Upsert a user fair share weight."""
        spec = UserFairShareUpserterSpec(
            resource_group=action.resource_group,
            user_uuid=action.user_uuid,
            project_id=action.project_id,
            domain_name=action.domain_name,
            weight=TriState.from_graphql(action.weight),
        )
        upserter = Upserter(spec=spec)
        result = await self._repository.upsert_user_fair_share(upserter)
        return UpsertUserFairShareWeightActionResult(data=result)
