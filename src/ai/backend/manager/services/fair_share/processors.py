"""Fair Share Processors."""

from __future__ import annotations

from typing import override

from ai.backend.manager.actions.monitors.monitor import ActionMonitor
from ai.backend.manager.actions.processor import ActionProcessor
from ai.backend.manager.actions.types import AbstractProcessorPackage, ActionSpec

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
    SearchDomainFairSharesAction,
    SearchDomainFairSharesActionResult,
    SearchProjectFairSharesAction,
    SearchProjectFairSharesActionResult,
    SearchRGDomainFairSharesAction,
    SearchRGDomainFairSharesActionResult,
    SearchRGProjectFairSharesAction,
    SearchRGProjectFairSharesActionResult,
    SearchRGUserFairSharesAction,
    SearchRGUserFairSharesActionResult,
    SearchUserFairSharesAction,
    SearchUserFairSharesActionResult,
    UpsertDomainFairShareWeightAction,
    UpsertDomainFairShareWeightActionResult,
    UpsertProjectFairShareWeightAction,
    UpsertProjectFairShareWeightActionResult,
    UpsertUserFairShareWeightAction,
    UpsertUserFairShareWeightActionResult,
)
from .service import FairShareService

__all__ = ("FairShareProcessors",)


class FairShareProcessors(AbstractProcessorPackage):
    """Processor package for fair share operations."""

    # Domain Fair Share
    get_domain_fair_share: ActionProcessor[GetDomainFairShareAction, GetDomainFairShareActionResult]
    search_domain_fair_shares: ActionProcessor[
        SearchDomainFairSharesAction, SearchDomainFairSharesActionResult
    ]
    search_rg_domain_fair_shares: ActionProcessor[
        SearchRGDomainFairSharesAction, SearchRGDomainFairSharesActionResult
    ]

    # Project Fair Share
    get_project_fair_share: ActionProcessor[
        GetProjectFairShareAction, GetProjectFairShareActionResult
    ]
    search_project_fair_shares: ActionProcessor[
        SearchProjectFairSharesAction, SearchProjectFairSharesActionResult
    ]
    search_rg_project_fair_shares: ActionProcessor[
        SearchRGProjectFairSharesAction, SearchRGProjectFairSharesActionResult
    ]

    # User Fair Share
    get_user_fair_share: ActionProcessor[GetUserFairShareAction, GetUserFairShareActionResult]
    search_user_fair_shares: ActionProcessor[
        SearchUserFairSharesAction, SearchUserFairSharesActionResult
    ]
    search_rg_user_fair_shares: ActionProcessor[
        SearchRGUserFairSharesAction, SearchRGUserFairSharesActionResult
    ]

    # Upsert Weight
    upsert_domain_fair_share_weight: ActionProcessor[
        UpsertDomainFairShareWeightAction, UpsertDomainFairShareWeightActionResult
    ]
    upsert_project_fair_share_weight: ActionProcessor[
        UpsertProjectFairShareWeightAction, UpsertProjectFairShareWeightActionResult
    ]
    upsert_user_fair_share_weight: ActionProcessor[
        UpsertUserFairShareWeightAction, UpsertUserFairShareWeightActionResult
    ]

    # Bulk Upsert Weight
    bulk_upsert_domain_fair_share_weight: ActionProcessor[
        BulkUpsertDomainFairShareWeightAction, BulkUpsertDomainFairShareWeightActionResult
    ]
    bulk_upsert_project_fair_share_weight: ActionProcessor[
        BulkUpsertProjectFairShareWeightAction, BulkUpsertProjectFairShareWeightActionResult
    ]
    bulk_upsert_user_fair_share_weight: ActionProcessor[
        BulkUpsertUserFairShareWeightAction, BulkUpsertUserFairShareWeightActionResult
    ]

    def __init__(self, service: FairShareService, action_monitors: list[ActionMonitor]) -> None:
        # Domain Fair Share
        self.get_domain_fair_share = ActionProcessor(service.get_domain_fair_share, action_monitors)
        self.search_domain_fair_shares = ActionProcessor(
            service.search_domain_fair_shares, action_monitors
        )
        self.search_rg_domain_fair_shares = ActionProcessor(
            service.search_rg_domain_fair_shares, action_monitors
        )

        # Project Fair Share
        self.get_project_fair_share = ActionProcessor(
            service.get_project_fair_share, action_monitors
        )
        self.search_project_fair_shares = ActionProcessor(
            service.search_project_fair_shares, action_monitors
        )
        self.search_rg_project_fair_shares = ActionProcessor(
            service.search_rg_project_fair_shares, action_monitors
        )

        # User Fair Share
        self.get_user_fair_share = ActionProcessor(service.get_user_fair_share, action_monitors)
        self.search_user_fair_shares = ActionProcessor(
            service.search_user_fair_shares, action_monitors
        )
        self.search_rg_user_fair_shares = ActionProcessor(
            service.search_rg_user_fair_shares, action_monitors
        )

        # Upsert Weight
        self.upsert_domain_fair_share_weight = ActionProcessor(
            service.upsert_domain_fair_share_weight, action_monitors
        )
        self.upsert_project_fair_share_weight = ActionProcessor(
            service.upsert_project_fair_share_weight, action_monitors
        )
        self.upsert_user_fair_share_weight = ActionProcessor(
            service.upsert_user_fair_share_weight, action_monitors
        )

        # Bulk Upsert Weight
        self.bulk_upsert_domain_fair_share_weight = ActionProcessor(
            service.bulk_upsert_domain_fair_share_weight, action_monitors
        )
        self.bulk_upsert_project_fair_share_weight = ActionProcessor(
            service.bulk_upsert_project_fair_share_weight, action_monitors
        )
        self.bulk_upsert_user_fair_share_weight = ActionProcessor(
            service.bulk_upsert_user_fair_share_weight, action_monitors
        )

    @override
    def supported_actions(self) -> list[ActionSpec]:
        return [
            # Domain
            GetDomainFairShareAction.spec(),
            SearchDomainFairSharesAction.spec(),
            SearchRGDomainFairSharesAction.spec(),
            # Project
            GetProjectFairShareAction.spec(),
            SearchProjectFairSharesAction.spec(),
            SearchRGProjectFairSharesAction.spec(),
            # User
            GetUserFairShareAction.spec(),
            SearchUserFairSharesAction.spec(),
            SearchRGUserFairSharesAction.spec(),
            # Upsert Weight
            UpsertDomainFairShareWeightAction.spec(),
            UpsertProjectFairShareWeightAction.spec(),
            UpsertUserFairShareWeightAction.spec(),
            # Bulk Upsert Weight
            BulkUpsertDomainFairShareWeightAction.spec(),
            BulkUpsertProjectFairShareWeightAction.spec(),
            BulkUpsertUserFairShareWeightAction.spec(),
        ]
