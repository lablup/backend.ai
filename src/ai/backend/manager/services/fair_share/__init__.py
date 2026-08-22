"""Fair Share Service package."""

from .actions import (
    BulkUpsertDomainFairShareWeightAction,
    BulkUpsertDomainFairShareWeightActionResult,
    BulkUpsertProjectFairShareWeightAction,
    BulkUpsertProjectFairShareWeightActionResult,
    BulkUpsertUserFairShareWeightAction,
    BulkUpsertUserFairShareWeightActionResult,
    DomainWeightInput,
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
    ProjectWeightInput,
    SearchRGDomainFairSharesAction,
    SearchRGDomainFairSharesActionResult,
    SearchRGProjectFairSharesAction,
    SearchRGProjectFairSharesActionResult,
    SearchRGUserFairSharesAction,
    SearchRGUserFairSharesActionResult,
    UserWeightInput,
)
from .processors import FairShareProcessors
from .service import FairShareService

__all__ = (
    # Service
    "FairShareService",
    # Processors
    "FairShareProcessors",
    # Domain Actions
    "GetDomainFairShareAction",
    "GetDomainFairShareActionResult",
    "GlobalSearchDomainFairSharesAction",
    "GlobalSearchDomainFairSharesActionResult",
    "SearchRGDomainFairSharesAction",
    "SearchRGDomainFairSharesActionResult",
    "BulkUpsertDomainFairShareWeightAction",
    "BulkUpsertDomainFairShareWeightActionResult",
    "DomainWeightInput",
    # Project Actions
    "GetProjectFairShareAction",
    "GetProjectFairShareActionResult",
    "GlobalSearchProjectFairSharesAction",
    "GlobalSearchProjectFairSharesActionResult",
    "SearchRGProjectFairSharesAction",
    "SearchRGProjectFairSharesActionResult",
    "BulkUpsertProjectFairShareWeightAction",
    "BulkUpsertProjectFairShareWeightActionResult",
    "ProjectWeightInput",
    # User Actions
    "GetUserFairShareAction",
    "GetUserFairShareActionResult",
    "GlobalSearchUserFairSharesAction",
    "GlobalSearchUserFairSharesActionResult",
    "SearchRGUserFairSharesAction",
    "SearchRGUserFairSharesActionResult",
    "BulkUpsertUserFairShareWeightAction",
    "BulkUpsertUserFairShareWeightActionResult",
    "UserWeightInput",
)
