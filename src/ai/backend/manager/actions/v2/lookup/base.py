from abc import ABC, abstractmethod
from typing import Any

from ai.backend.common.data.entity.types import EntityIdentifier, EntityType
from ai.backend.manager.actions.types import ActionOperationType

__all__ = ("LookupKey", "BaseLookupAction", "BaseLookupActionResult")


class LookupKey(ABC):
    """The external key a lookup resolves.

    Keys come in several shapes — ``canonical`` + ``architecture``, ``domain_name`` +
    ``email``, a bare ``name`` — so no fixed set of columns fits them.
    """

    @abstractmethod
    def kind(self) -> str:
        """Return the key's shape, never its value.

        The lookup metric is keyed by this. Values would blow up its cardinality, and
        the shape is what says which lookups still exist.
        """
        raise NotImplementedError

    @abstractmethod
    def to_dict(self) -> dict[str, Any]:
        """Return the key's components, for the audit record."""
        raise NotImplementedError


class BaseLookupAction(ABC):
    """Base for actions that turn an external key into an internal id.

    Declares no target: producing one is the whole point of the run, so there is
    nothing for RBAC to resolve against. Authentication is the only gate, and the
    action that follows is responsible for authorization.
    """

    @classmethod
    @abstractmethod
    def entity_type(cls) -> EntityType:
        """Return the type of entity being looked up."""
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def action_name(cls) -> str:
        """Return the name recorded on audit rows: a lowercase snake_case verb phrase,
        declared rather than derived so a class rename cannot split the recorded
        history. Naming rule: services/AGENTS.md."""
        raise NotImplementedError

    @abstractmethod
    def lookup_key(self) -> LookupKey:
        """Return the key being resolved."""
        raise NotImplementedError

    @classmethod
    def operation_type(cls) -> ActionOperationType:
        """Its own operation, so the audit trail can tell a key resolution from a read by id.

        Still a read, so it follows the audit rules for reads.
        """
        return ActionOperationType.LOOKUP


class BaseLookupActionResult(ABC):
    @abstractmethod
    def entity_id(self) -> EntityIdentifier:
        """Return the id the key names."""
        raise NotImplementedError
