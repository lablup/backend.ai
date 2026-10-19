from __future__ import annotations

from ai.backend.manager.actions.registry.field import FieldGroup
from ai.backend.manager.actions.v2.ops.result import ScopedFieldsOpsResult
from ai.backend.manager.actions.v2.scope.processor import ScopeActionProcessor
from ai.backend.manager.data.dotfile.types import DotfileData
from ai.backend.manager.services.dotfile.actions.search import SearchDotfilesAction


class DotfileProcessors:
    """Dotfile operations straight against ops. The owner's kind is a value on the row,
    so the group comes from the registry rather than an entity's own group."""

    search: ScopeActionProcessor[SearchDotfilesAction, ScopedFieldsOpsResult[DotfileData]]

    def __init__(self, group: FieldGroup[DotfileData]) -> None:
        self.search = group.search_ops(SearchDotfilesAction)
