"""Generic, entity-agnostic lifecycle coordinator ABCs."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from uuid import UUID

from ai.backend.common.events.types import AbstractAnycastEvent
from ai.backend.manager.data.reconciler.types import (
    BaseReconcilerCategory,
    HandlerOutcome,
    LastHistory,
)
from ai.backend.manager.data.session.options import HandlerOptions
from ai.backend.manager.data.session.types import SchedulingResult
from ai.backend.manager.defs import LockID
from ai.backend.manager.metrics.reconciler import ReconcilerMetricObserver
from ai.backend.manager.sokovan.recorder.context import RecorderContext
from ai.backend.manager.sokovan.recorder.types import ExecutionRecord


class BaseReconcilerInfo(ABC):
    """Marker for entities that drive scheduling (vs. purely historical)"""

    @abstractmethod
    def entity_ids(self) -> Sequence[UUID]:
        """IDs of the entities that drive scheduling decisions."""
        raise NotImplementedError

    @abstractmethod
    def now(self) -> datetime:
        """DB-sourced current time read with the fetch (not per-server wall clock)."""
        raise NotImplementedError


class ReconcilerDecision(ABC):
    """Per-entity handler outcome the coordinator classifies into a final SchedulingResult.

    The handler sets ``outcome`` to SUCCESS/FAILURE/STALE/SKIPPED only; the coordinator
    refines FAILURE from the prior history (``last_*``) and the stage policy.
    """

    @abstractmethod
    def entity_id(self) -> UUID:
        raise NotImplementedError

    @abstractmethod
    def outcome(self) -> HandlerOutcome:
        raise NotImplementedError

    @abstractmethod
    def last_history(self) -> LastHistory | None:
        raise NotImplementedError


class BaseReconcilerResult(ABC):
    """Marker for scheduling handler results that drive scheduling decisions."""

    @abstractmethod
    def processed_count(self) -> int:
        """Number of entities successfully processed."""
        raise NotImplementedError

    @abstractmethod
    def failed_count(self) -> int:
        """Number of entities that failed processing."""
        raise NotImplementedError

    @abstractmethod
    def decisions(self) -> Sequence[ReconcilerDecision]:
        """Per-entity outcomes the coordinator resolves before the applier runs."""
        raise NotImplementedError


class BaseReconcilerTargetStatuses(ABC):
    pass


class BaseReconcilerKind(StrEnum):
    pass


class ReconcilerSource[
    Info: BaseReconcilerInfo,
    Category: BaseReconcilerCategory,
    TargetStatuses: BaseReconcilerTargetStatuses,
](ABC):
    """Source of scheduling entities for one lifecycle stage, keyed by the handler's declared category and target statuses."""

    @abstractmethod
    async def fetch_reconcile_info(
        self,
        category: Category,
        target_statuses: TargetStatuses,
    ) -> Info:
        """Fetch entities that drive scheduling for the given category and target statuses."""
        raise NotImplementedError


class ReconcilerHandler[
    Info: BaseReconcilerInfo,
    Result: BaseReconcilerResult,
](ABC):
    @abstractmethod
    async def execute(self, reconcile_info: Info) -> Result:
        """Run the stage over the fetched entities."""
        raise NotImplementedError

    @abstractmethod
    async def post_process(self, result: Result) -> None:
        """Side effects after transitions are applied."""
        raise NotImplementedError


@dataclass(frozen=True)
class ReconcilerStageMetadata[
    Category: BaseReconcilerCategory,
    Kind: BaseReconcilerKind,
    TargetStatuses: BaseReconcilerTargetStatuses,
    Status,
]:
    """Stage definition the applier reads from: metrics labeling, fetch scope, history
    descriptor (category/phase), and the per-result target-status map."""

    category: Category
    kind: Kind
    target_statuses: TargetStatuses
    name: str
    phase: str
    lock_id: LockID | None
    policy: HandlerOptions
    transitions: Mapping[SchedulingResult, Status]


@dataclass(frozen=True)
class ReconcilerApplyInput[
    Result: BaseReconcilerResult,
    Category: BaseReconcilerCategory,
    Kind: BaseReconcilerKind,
    TargetStatuses: BaseReconcilerTargetStatuses,
    Status,
]:
    """Everything the applier needs for one tick: the handler result (which carries each
    decision's own input state), the recorded sub-steps, the coordinator-resolved
    per-entity results, and the stage metadata (category/phase/transitions)."""

    result: Result
    records: Mapping[UUID, ExecutionRecord]
    classified: Mapping[UUID, SchedulingResult]
    metadata: ReconcilerStageMetadata[Category, Kind, TargetStatuses, Status]


class ReconcilerApplier[
    Result: BaseReconcilerResult,
    Category: BaseReconcilerCategory,
    Kind: BaseReconcilerKind,
    TargetStatuses: BaseReconcilerTargetStatuses,
    Status,
](ABC):
    """Applies scheduling decisions derived from a handler's result."""

    @abstractmethod
    async def apply(
        self,
        apply_input: ReconcilerApplyInput[Result, Category, Kind, TargetStatuses, Status],
    ) -> None:
        """Persist scheduling decisions derived from the handler result."""
        raise NotImplementedError


class ReconcilerStageRunner(ABC):
    """Type-erased stage view the coordinator dispatches; carries no entity types."""

    @property
    @abstractmethod
    def lock_id(self) -> LockID | None:
        """Lock to acquire before running, or None."""
        raise NotImplementedError

    @abstractmethod
    async def run(self) -> None:
        """Fetch -> execute -> apply -> post_process."""
        raise NotImplementedError


class ReconcilerStage[
    Info: BaseReconcilerInfo,
    Result: BaseReconcilerResult,
    Category: BaseReconcilerCategory,
    TargetStatuses: BaseReconcilerTargetStatuses,
    Kind: BaseReconcilerKind,
    Status,
](ReconcilerStageRunner):
    """One lifecycle stage for scheduling decisions, with injected handler, source, applier, and metadata for metrics and locking."""

    _handler: ReconcilerHandler[Info, Result]
    _source: ReconcilerSource[Info, Category, TargetStatuses]
    _applier: ReconcilerApplier[Result, Category, Kind, TargetStatuses, Status]
    _metadata: ReconcilerStageMetadata[Category, Kind, TargetStatuses, Status]

    def __init__(
        self,
        handler: ReconcilerHandler[Info, Result],
        source: ReconcilerSource[Info, Category, TargetStatuses],
        applier: ReconcilerApplier[Result, Category, Kind, TargetStatuses, Status],
        metadata: ReconcilerStageMetadata[Category, Kind, TargetStatuses, Status],
    ) -> None:
        self._handler = handler
        self._source = source
        self._applier = applier
        self._metadata = metadata

    @property
    def lock_id(self) -> LockID | None:
        return self._metadata.lock_id

    async def run(self) -> None:
        metrics = ReconcilerMetricObserver.instance()
        kind = self._metadata.kind
        handler_name = self._metadata.name
        with metrics.measure(kind, handler_name, "fetch_scheduling_entities"):
            reconcile_info = await self._source.fetch_reconcile_info(
                self._metadata.category, self._metadata.target_statuses
            )
        ids = reconcile_info.entity_ids()
        with RecorderContext[UUID].scope(handler_name, ids) as pool:
            with metrics.measure(kind, handler_name, "execute_handler"):
                result = await self._handler.execute(reconcile_info)
            metrics.observe_processed(
                kind, handler_name, result.processed_count(), result.failed_count()
            )
            records = pool.build_all_records()
            with metrics.measure(kind, handler_name, "classify_scheduling_results"):
                classified = self._classify(result, reconcile_info.now())
            with metrics.measure(kind, handler_name, "apply_scheduling_decisions"):
                await self._applier.apply(
                    ReconcilerApplyInput(
                        result=result,
                        records=records,
                        classified=classified,
                        metadata=self._metadata,
                    )
                )
        with metrics.measure(kind, handler_name, "post_process"):
            await self._handler.post_process(result)

    def _classify(self, result: Result, now: datetime) -> Mapping[UUID, SchedulingResult]:
        return {
            decision.entity_id(): self._classify_outcome(decision, now)
            for decision in result.decisions()
        }

    def _classify_outcome(self, decision: ReconcilerDecision, now: datetime) -> SchedulingResult:
        # Only FAILURE is refined (against prior history, reset on phase change, + policy);
        # the rest map straight through to their SchedulingResult counterpart.
        match decision.outcome():
            case HandlerOutcome.SUCCESS:
                return SchedulingResult.SUCCESS
            case HandlerOutcome.STALE:
                return SchedulingResult.STALE
            case HandlerOutcome.SKIPPED:
                return SchedulingResult.SKIPPED
            case HandlerOutcome.FAILURE:
                last = decision.last_history()
                if last is not None and last.phase == self._metadata.phase:
                    attempts = last.attempts
                    started_at: datetime | None = last.started_at
                else:
                    attempts = 0
                    started_at = None
                policy = self._metadata.policy
                if policy.is_retry_exhausted(attempts):
                    return SchedulingResult.GIVE_UP
                if policy.is_timed_out(started_at, now):
                    return SchedulingResult.EXPIRED
                return SchedulingResult.NEED_RETRY


@dataclass
class ReconcilerTaskSpec:
    """Short/long tick spec for one reconcile type with injected event factories."""

    reconcile_type: str
    if_needed_event_factory: Callable[[str], AbstractAnycastEvent]
    process_event_factory: Callable[[str], AbstractAnycastEvent]
    short_interval: float | None = None
    long_interval: float = 60.0
    initial_delay: float = 30.0

    def create_if_needed_event(self) -> AbstractAnycastEvent:
        return self.if_needed_event_factory(self.reconcile_type)

    def create_process_event(self) -> AbstractAnycastEvent:
        return self.process_event_factory(self.reconcile_type)

    @property
    def short_task_name(self) -> str:
        return f"reconcile_process_if_needed_{self.reconcile_type}"

    @property
    def long_task_name(self) -> str:
        return f"reconcile_process_{self.reconcile_type}"
