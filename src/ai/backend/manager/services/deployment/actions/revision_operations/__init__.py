"""Revision operations action definitions."""

from .activate_revision import (
    ActivateRevisionAction,
    ActivateRevisionActionResult,
)
from .promote_deployment import (
    PromoteDeploymentAction,
    PromoteDeploymentActionResult,
)

__all__ = [
    "ActivateRevisionAction",
    "ActivateRevisionActionResult",
    "PromoteDeploymentAction",
    "PromoteDeploymentActionResult",
]
