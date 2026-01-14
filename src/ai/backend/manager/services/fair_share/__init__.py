"""Fair Share Service package."""

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
)
from .service import FairShareService

__all__ = (
    # Service
    "FairShareService",
    # Domain Actions
    "GetDomainFairShareAction",
    "GetDomainFairShareActionResult",
    "SearchDomainFairSharesAction",
    "SearchDomainFairSharesActionResult",
    # Project Actions
    "GetProjectFairShareAction",
    "GetProjectFairShareActionResult",
    "SearchProjectFairSharesAction",
    "SearchProjectFairSharesActionResult",
    # User Actions
    "GetUserFairShareAction",
    "GetUserFairShareActionResult",
    "SearchUserFairSharesAction",
    "SearchUserFairSharesActionResult",
)
