"""A scope item a search names, when the caller may name one of several kinds."""

from abc import ABC, abstractmethod

from ai.backend.common.data.entity.types import ScopeRef
from ai.backend.manager.models.scopes import OperationScope


class SearchableScopeTarget(ABC):
    """One thing a scoped search may be bounded by.

    A read whose caller picks among several kinds of bound — a session or the kernel
    inside it, a deployment or one of its replica groups — carries the choice as a
    value rather than as a separate action per kind. The two hooks are the two axes:
    which scope answers for the read, and which rows it looks at.
    """

    @abstractmethod
    def to_scope_ref(self) -> ScopeRef:
        """Return the scope the read is answered for."""
        raise NotImplementedError

    @abstractmethod
    def to_search_scope(self) -> OperationScope:
        """Return the condition narrowing the rows the read returns."""
        raise NotImplementedError
