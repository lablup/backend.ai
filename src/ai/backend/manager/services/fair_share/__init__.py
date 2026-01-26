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
    ProjectWeightInput,
    SearchDomainFairSharesAction,
    SearchDomainFairSharesActionResult,
    SearchProjectFairSharesAction,
    SearchProjectFairSharesActionResult,
    SearchUserFairSharesAction,
    SearchUserFairSharesActionResult,
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
    "SearchDomainFairSharesAction",
    "SearchDomainFairSharesActionResult",
    "BulkUpsertDomainFairShareWeightAction",
    "BulkUpsertDomainFairShareWeightActionResult",
    "DomainWeightInput",
    # Project Actions
    "GetProjectFairShareAction",
    "GetProjectFairShareActionResult",
    "SearchProjectFairSharesAction",
    "SearchProjectFairSharesActionResult",
    "BulkUpsertProjectFairShareWeightAction",
    "BulkUpsertProjectFairShareWeightActionResult",
    "ProjectWeightInput",
    # User Actions
    "GetUserFairShareAction",
    "GetUserFairShareActionResult",
    "SearchUserFairSharesAction",
    "SearchUserFairSharesActionResult",
    "BulkUpsertUserFairShareWeightAction",
    "BulkUpsertUserFairShareWeightActionResult",
    "UserWeightInput",
)
