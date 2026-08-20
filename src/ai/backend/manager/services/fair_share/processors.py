"""Fair Share Processors."""

from __future__ import annotations

from typing import Any

from ai.backend.manager.actions.registry import ProcessorGroup
from ai.backend.manager.actions.v2.global_scope.processor import GlobalActionProcessor
from ai.backend.manager.actions.v2.scope.processor import ScopeActionProcessor

from .actions import (
    BulkUpsertDomainFairShareWeightAction,
    BulkUpsertDomainFairShareWeightActionResult,
    BulkUpsertProjectFairShareWeightAction,
    BulkUpsertProjectFairShareWeightActionResult,
    BulkUpsertUserFairShareWeightAction,
    BulkUpsertUserFairShareWeightActionResult,
    GetDomainFairShareAction,
    GetDomainFairShareActionResult,
    GetProjectFairShareAction,
    GetProjectFairShareActionResult,
    GetUserFairShareAction,
    GetUserFairShareActionResult,
    GlobalSearchDomainFairSharesAction,
    GlobalSearchDomainFairSharesActionResult,
    GlobalSearchProjectFairSharesAction,
    GlobalSearchProjectFairSharesActionResult,
    GlobalSearchUserFairSharesAction,
    GlobalSearchUserFairSharesActionResult,
    SearchRGDomainFairSharesAction,
    SearchRGDomainFairSharesActionResult,
    SearchRGProjectFairSharesAction,
    SearchRGProjectFairSharesActionResult,
    SearchRGUserFairSharesAction,
    SearchRGUserFairSharesActionResult,
    UpsertDomainFairShareWeightAction,
    UpsertDomainFairShareWeightActionResult,
    UpsertProjectFairShareWeightAction,
    UpsertProjectFairShareWeightActionResult,
    UpsertUserFairShareWeightAction,
    UpsertUserFairShareWeightActionResult,
)
from .service import FairShareService

__all__ = ("FairShareProcessors",)


class FairShareProcessors:
    """Processor package for fair share operations."""

    # Domain Fair Share
    get_domain_fair_share: ScopeActionProcessor[
        GetDomainFairShareAction, GetDomainFairShareActionResult
    ]
    search_domain_fair_shares: GlobalActionProcessor[
        GlobalSearchDomainFairSharesAction, GlobalSearchDomainFairSharesActionResult
    ]
    search_rg_domain_fair_shares: ScopeActionProcessor[
        SearchRGDomainFairSharesAction, SearchRGDomainFairSharesActionResult
    ]

    # Project Fair Share
    get_project_fair_share: ScopeActionProcessor[
        GetProjectFairShareAction, GetProjectFairShareActionResult
    ]
    search_project_fair_shares: GlobalActionProcessor[
        GlobalSearchProjectFairSharesAction, GlobalSearchProjectFairSharesActionResult
    ]
    search_rg_project_fair_shares: ScopeActionProcessor[
        SearchRGProjectFairSharesAction, SearchRGProjectFairSharesActionResult
    ]

    # User Fair Share
    get_user_fair_share: ScopeActionProcessor[GetUserFairShareAction, GetUserFairShareActionResult]
    search_user_fair_shares: GlobalActionProcessor[
        GlobalSearchUserFairSharesAction, GlobalSearchUserFairSharesActionResult
    ]
    search_rg_user_fair_shares: ScopeActionProcessor[
        SearchRGUserFairSharesAction, SearchRGUserFairSharesActionResult
    ]

    # Upsert Weight
    upsert_domain_fair_share_weight: ScopeActionProcessor[
        UpsertDomainFairShareWeightAction, UpsertDomainFairShareWeightActionResult
    ]
    upsert_project_fair_share_weight: ScopeActionProcessor[
        UpsertProjectFairShareWeightAction, UpsertProjectFairShareWeightActionResult
    ]
    upsert_user_fair_share_weight: ScopeActionProcessor[
        UpsertUserFairShareWeightAction, UpsertUserFairShareWeightActionResult
    ]

    # Bulk Upsert Weight
    bulk_upsert_domain_fair_share_weight: ScopeActionProcessor[
        BulkUpsertDomainFairShareWeightAction, BulkUpsertDomainFairShareWeightActionResult
    ]
    bulk_upsert_project_fair_share_weight: ScopeActionProcessor[
        BulkUpsertProjectFairShareWeightAction, BulkUpsertProjectFairShareWeightActionResult
    ]
    bulk_upsert_user_fair_share_weight: ScopeActionProcessor[
        BulkUpsertUserFairShareWeightAction, BulkUpsertUserFairShareWeightActionResult
    ]

    def __init__(
        self,
        domain: ProcessorGroup[Any],
        project: ProcessorGroup[Any],
        user: ProcessorGroup[Any],
        service: FairShareService,
    ) -> None:
        # Domain Fair Share
        self.get_domain_fair_share = domain.scope(
            GetDomainFairShareAction, service.get_domain_fair_share
        )
        self.search_domain_fair_shares = domain.global_scope(
            GlobalSearchDomainFairSharesAction, service.search_domain_fair_shares
        )
        self.search_rg_domain_fair_shares = domain.scope(
            SearchRGDomainFairSharesAction, service.search_rg_domain_fair_shares
        )

        # Project Fair Share
        self.get_project_fair_share = project.scope(
            GetProjectFairShareAction, service.get_project_fair_share
        )
        self.search_project_fair_shares = project.global_scope(
            GlobalSearchProjectFairSharesAction, service.search_project_fair_shares
        )
        self.search_rg_project_fair_shares = project.scope(
            SearchRGProjectFairSharesAction, service.search_rg_project_fair_shares
        )

        # User Fair Share
        self.get_user_fair_share = user.scope(GetUserFairShareAction, service.get_user_fair_share)
        self.search_user_fair_shares = user.global_scope(
            GlobalSearchUserFairSharesAction, service.search_user_fair_shares
        )
        self.search_rg_user_fair_shares = user.scope(
            SearchRGUserFairSharesAction, service.search_rg_user_fair_shares
        )

        # Upsert Weight
        self.upsert_domain_fair_share_weight = domain.scope(
            UpsertDomainFairShareWeightAction, service.upsert_domain_fair_share_weight
        )
        self.upsert_project_fair_share_weight = project.scope(
            UpsertProjectFairShareWeightAction, service.upsert_project_fair_share_weight
        )
        self.upsert_user_fair_share_weight = user.scope(
            UpsertUserFairShareWeightAction, service.upsert_user_fair_share_weight
        )

        # Bulk Upsert Weight
        self.bulk_upsert_domain_fair_share_weight = domain.scope(
            BulkUpsertDomainFairShareWeightAction, service.bulk_upsert_domain_fair_share_weight
        )
        self.bulk_upsert_project_fair_share_weight = project.scope(
            BulkUpsertProjectFairShareWeightAction, service.bulk_upsert_project_fair_share_weight
        )
        self.bulk_upsert_user_fair_share_weight = user.scope(
            BulkUpsertUserFairShareWeightAction, service.bulk_upsert_user_fair_share_weight
        )
