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
