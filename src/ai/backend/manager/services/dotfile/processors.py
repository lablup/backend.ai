from __future__ import annotations

from ai.backend.manager.actions.registry.field import LookupFieldGroup
from ai.backend.manager.actions.v2.field.processor import SingleFieldActionProcessor
from ai.backend.manager.actions.v2.ops.result import EntityOpsResult, ScopedFieldsOpsResult
from ai.backend.manager.actions.v2.scope.processor import ScopeActionProcessor
from ai.backend.manager.data.dotfile.types import DotfileData
from ai.backend.manager.services.dotfile.actions.purge import PurgeDotfileAction
from ai.backend.manager.services.dotfile.actions.search import SearchDotfilesAction
from ai.backend.manager.services.dotfile.actions.update import UpdateDotfileAction


class DotfileProcessors:
    """Dotfile operations straight against ops. The owner's kind is a value on the row,
    so the group comes from the registry rather than an entity's own group."""

    search: ScopeActionProcessor[SearchDotfilesAction, ScopedFieldsOpsResult[DotfileData]]
    update: SingleFieldActionProcessor[UpdateDotfileAction, EntityOpsResult[DotfileData]]
    purge: SingleFieldActionProcessor[PurgeDotfileAction, EntityOpsResult[DotfileData]]

    def __init__(self, group: LookupFieldGroup[DotfileData]) -> None:
        self.search = group.search_ops(SearchDotfilesAction)
        self.update = group.runtime_update_ops(UpdateDotfileAction)
        self.purge = group.runtime_purge_ops(PurgeDotfileAction)
