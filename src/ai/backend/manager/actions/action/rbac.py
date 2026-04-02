"""RBAC action base class for permission declarations."""

import enum
from abc import ABC, abstractmethod
from dataclasses import dataclass

from ai.backend.common.data.permission.types import OperationType, RBACElementType


class RBACActionName(enum.StrEnum):
    """All known RBAC action names."""

    CREATE = "create"
    GET = "get"
    SEARCH = "search"
    UPDATE = "update"
    SOFT_DELETE = "soft_delete"
    HARD_DELETE = "hard_delete"
    GRANT_ALL = "grant_all"
    GRANT_READ = "grant_read"
    GRANT_UPDATE = "grant_update"
    GRANT_SOFT_DELETE = "grant_soft_delete"
    GRANT_HARD_DELETE = "grant_hard_delete"


@dataclass(frozen=True)
class RBACRequiredPermission:
    """The RBAC permission required to execute an action."""

    element_type: RBACElementType
    operation: OperationType


def build_operation_description(
    action_name: RBACActionName,
    element_type: RBACElementType,
) -> str:
    """Build a human-readable description from action name and element type."""
    entity = element_type.value.replace("_", " ")
    match action_name:
        case RBACActionName.CREATE:
            return f"Create a new {entity}"
        case RBACActionName.GET:
            return f"Get {entity} details"
        case RBACActionName.SEARCH:
            return f"Search {entity} list"
        case RBACActionName.UPDATE:
            return f"Update {entity}"
        case RBACActionName.SOFT_DELETE:
            return f"Soft-delete {entity}"
        case RBACActionName.HARD_DELETE:
            return f"Hard-delete {entity}"
        case RBACActionName.GRANT_ALL:
            return f"Grant all permissions for {entity}"
        case RBACActionName.GRANT_READ:
            return f"Grant read permission for {entity}"
        case RBACActionName.GRANT_UPDATE:
            return f"Grant update permission for {entity}"
        case RBACActionName.GRANT_SOFT_DELETE:
            return f"Grant soft-delete permission for {entity}"
        case RBACActionName.GRANT_HARD_DELETE:
            return f"Grant hard-delete permission for {entity}"


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

    @classmethod
    @abstractmethod
    def permission_scope(cls) -> RBACElementType:
        """Return the scope type where this action's permission is evaluated.

        Each RBAC action class represents a unique (scope, entity, operation)
        triple.  The scope is the context in which the permission check occurs
        (e.g. PROJECT, USER, DOMAIN).
        """
        ...
