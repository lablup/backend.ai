"""RBAC action base class for permission declarations."""

from abc import ABC, abstractmethod

from ai.backend.common.data.permission.types import OperationType, RBACElementType


class BaseRBACAction(ABC):
    """
    Abstract base class for RBAC actions.

    This class defines the interface for action classes to declare their
    required RBAC permission. It is NOT part of the main action inheritance
    hierarchy (BaseAction, BaseScopeAction, etc.).

    Concrete implementations (BA-5317~BA-5348) will inherit from this class
    and declare what RBAC permission they require.
    """

    @classmethod
    @abstractmethod
    def required_permission(cls) -> tuple[RBACElementType, OperationType]:
        """
        Return the RBAC permission required by this action.

        Returns:
            tuple[RBACElementType, OperationType]: (target element type, required operation)

        Example:
            (RBACElementType.USER, OperationType.READ)
        """
        ...
