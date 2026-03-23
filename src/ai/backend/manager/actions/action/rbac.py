"""RBAC action base class for permission declarations."""

import enum
from abc import ABC, abstractmethod
from dataclasses import dataclass

from ai.backend.common.data.permission.types import OperationType, RBACElementType


class RBACActionName(enum.StrEnum):
    """All known RBAC action names."""


@dataclass(frozen=True)
class RBACRequiredPermission:
    """The RBAC permission required to execute an action."""

    element_type: RBACElementType
    operation: OperationType


class BaseRBACAction(ABC):
    """
    Abstract base class for RBAC actions.

    Defines the interface for action classes to declare their required RBAC
    permission. This is NOT part of the main action inheritance hierarchy
    (BaseAction, BaseScopeAction, etc.).
    """

    @classmethod
    @abstractmethod
    def action_name(cls) -> RBACActionName:
        """Return the action name for this action."""
        ...

    @classmethod
    @abstractmethod
    def required_permission(cls) -> RBACRequiredPermission:
        """Return the RBAC permission required by this action."""
        ...
