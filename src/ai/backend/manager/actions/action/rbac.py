"""RBAC action base class for entity-operation mappings."""

from abc import ABC, abstractmethod
from collections.abc import Mapping

from ai.backend.common.data.permission.types import EntityType
from ai.backend.manager.actions.types import ActionOperationType


class BaseRBACAction(ABC):
    """
    Abstract base class for RBAC actions.

    This class defines the interface for entity-specific RBAC action classes
    that provide valid operation mappings. It is NOT part of the main action
    inheritance hierarchy (BaseAction, BaseScopeAction, etc.).

    Concrete implementations (BA-5317~BA-5348) will inherit from this class
    and provide entity-specific valid operations.
    """

    @classmethod
    @abstractmethod
    def entity_type(cls) -> EntityType:
        """
        Return the EntityType this RBAC action class represents.

        Returns:
            EntityType: The entity type (e.g., EntityType.USER, EntityType.VFOLDER)
        """
        ...

    @classmethod
    @abstractmethod
    def valid_operations(cls) -> Mapping[ActionOperationType, str]:
        """
        Return a mapping of valid operations for this entity type.

        The mapping keys are ActionOperationType values (GET, SEARCH, CREATE, etc.)
        and values are human-readable descriptions of what each operation does.

        Returns:
            Mapping[ActionOperationType, str]: Valid operations with descriptions

        Example:
            {
                ActionOperationType.GET: "Get user details",
                ActionOperationType.SEARCH: "Search users",
                ActionOperationType.CREATE: "Create new user",
                ActionOperationType.UPDATE: "Update user information",
                ActionOperationType.DELETE: "Delete user",
            }
        """
        ...
