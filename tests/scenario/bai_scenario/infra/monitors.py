"""Action recording: which actions a run executed, for comparing test suites.

One recorder shared by one small monitor per processor shape. Set
``BACKEND_ACTION_RECORD_FILE`` to append every record as a JSON line, so two pytest
runs (legacy component tests and the scenario table) can be compared afterwards.
"""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field
from typing import Any, override

from ai.backend.manager.actions.action.base import BaseAction, BaseActionTriggerMeta, ProcessResult
from ai.backend.manager.actions.monitors import ActionMonitors
from ai.backend.manager.actions.monitors.monitor import ActionMonitor
from ai.backend.manager.actions.v2.bulk.monitor.base import BulkActionMonitor
from ai.backend.manager.actions.v2.bulk.result import BulkActionProcessResult
from ai.backend.manager.actions.v2.bulk.trigger import BulkActionTriggerMeta
from ai.backend.manager.actions.v2.global_scope.base import BaseGlobalAction
from ai.backend.manager.actions.v2.global_scope.monitor.base import GlobalActionMonitor
from ai.backend.manager.actions.v2.global_scope.result import GlobalActionProcessResult
from ai.backend.manager.actions.v2.lookup.base import BaseLookupAction
from ai.backend.manager.actions.v2.lookup.monitor.base import LookupActionMonitor
from ai.backend.manager.actions.v2.lookup.result import LookupActionProcessResult
from ai.backend.manager.actions.v2.scope.base import BaseScopeAction
from ai.backend.manager.actions.v2.scope.monitor.base import ScopeActionMonitor
from ai.backend.manager.actions.v2.scope.result import ScopeActionProcessResult
from ai.backend.manager.actions.v2.single_entity.monitor.base import SingleEntityActionMonitor
from ai.backend.manager.actions.v2.single_entity.result import SingleEntityActionProcessResult
from ai.backend.manager.actions.v2.single_entity.trigger import SingleEntityActionTriggerMeta

RECORD_FILE_ENV = "BACKEND_ACTION_RECORD_FILE"


@dataclass(frozen=True)
class RecordedAction:
    shape: str
    action: str
    status: str

    def key(self) -> tuple[str, str]:
        return (self.shape, self.action)


@dataclass
class ActionRecorder:
    records: list[RecordedAction] = field(default_factory=list)
    suite: str = "scenario"

    def add(self, shape: str, action: str, status: Any) -> None:
        record = RecordedAction(shape, action, str(getattr(status, "value", status)))
        self.records.append(record)
        path = os.environ.get(RECORD_FILE_ENV)
        if path:
            with open(path, "a", encoding="utf8") as f:
                f.write(json.dumps({"suite": self.suite, **asdict(record)}) + "\n")

    def executed(self) -> set[tuple[str, str]]:
        return {r.key() for r in self.records}

    def monitors(self) -> ActionMonitors:
        return ActionMonitors(
            legacy=[_Legacy(self)],
            single_entity=[_SingleEntity(self)],
            bulk=[_Bulk(self)],
            scope=[_Scope(self)],
            global_scope=[_Global(self)],
            lookup=[_Lookup(self)],
        )


class _Legacy(ActionMonitor):
    def __init__(self, recorder: ActionRecorder) -> None:
        self._r = recorder

    @override
    async def prepare(self, action: BaseAction, meta: BaseActionTriggerMeta) -> None:
        return None

    @override
    async def done(self, action: BaseAction, result: ProcessResult) -> None:
        self._r.add("legacy", type(action).__name__, result.meta.status)


class _SingleEntity(SingleEntityActionMonitor):
    def __init__(self, recorder: ActionRecorder) -> None:
        self._r = recorder

    @override
    async def prepare(self, meta: SingleEntityActionTriggerMeta) -> None:
        return None

    @override
    async def done(
        self, meta: SingleEntityActionTriggerMeta, result: SingleEntityActionProcessResult
    ) -> None:
        self._r.add("single_entity", meta.action_name, result.meta.status)


class _Bulk(BulkActionMonitor):
    def __init__(self, recorder: ActionRecorder) -> None:
        self._r = recorder

    @override
    async def prepare(self, meta: BulkActionTriggerMeta) -> None:
        return None

    @override
    async def done(self, meta: BulkActionTriggerMeta, result: BulkActionProcessResult) -> None:
        self._r.add("bulk", meta.action_name, getattr(result.meta, "status", "unknown"))


class _Scope(ScopeActionMonitor):
    def __init__(self, recorder: ActionRecorder) -> None:
        self._r = recorder

    @override
    async def prepare(self, action: BaseScopeAction, meta: BaseActionTriggerMeta) -> None:
        return None

    @override
    async def done(self, action: BaseScopeAction, result: ScopeActionProcessResult) -> None:
        self._r.add("scope", action.action_name(), result.meta.status)


class _Global(GlobalActionMonitor):
    def __init__(self, recorder: ActionRecorder) -> None:
        self._r = recorder

    @override
    async def prepare(self, action: BaseGlobalAction, meta: BaseActionTriggerMeta) -> None:
        return None

    @override
    async def done(self, action: BaseGlobalAction, result: GlobalActionProcessResult) -> None:
        self._r.add("global", action.action_name(), result.meta.status)


class _Lookup(LookupActionMonitor):
    def __init__(self, recorder: ActionRecorder) -> None:
        self._r = recorder

    @override
    async def prepare(self, action: BaseLookupAction, meta: BaseActionTriggerMeta) -> None:
        return None

    @override
    async def done(self, action: BaseLookupAction, result: LookupActionProcessResult) -> None:
        self._r.add("lookup", action.action_name(), result.meta.status)
