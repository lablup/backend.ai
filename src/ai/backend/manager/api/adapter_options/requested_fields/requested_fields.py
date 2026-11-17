"""The data fields a request selected, handed from a transport to an adapter."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ai.backend.manager.errors.api import RequestedFieldNotDeclared
from ai.backend.manager.models.specs.search.field import QueryColumn
from ai.backend.manager.models.specs.search.query_spec import QueryOwnSection


@dataclass(frozen=True)
class RequestedFields:
    """Data field names a request selected. A read adds the id whether it is named or not."""

    names: frozenset[str]

    def columns(self, own: QueryOwnSection) -> list[QueryColumn[Any, Any, Any]]:
        """The columns of ``own`` named here, in declaration order."""
        declared = own.columns()
        undeclared = self.names - declared.keys()
        if undeclared:
            raise RequestedFieldNotDeclared(
                f"{type(own).__name__} declares no column for {sorted(undeclared)}"
            )
        return [column for name, column in declared.items() if name in self.names]
