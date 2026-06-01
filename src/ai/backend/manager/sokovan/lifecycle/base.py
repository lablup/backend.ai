"""Generic, entity-agnostic lifecycle coordinator ABCs."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from uuid import UUID

from ai.backend.common.events.types import AbstractAnycastEvent
from ai.backend.manager.defs import LockID
from ai.backend.manager.metrics.lifecycle import LifecycleMetricObserver
from ai.backend.manager.sokovan.recorder.context import RecorderContext
from ai.backend.manager.sokovan.recorder.types import ExecutionRecord


class LifecycleResult(ABC):
    """A lifecycle stage's outcome, exposing processed/failed counts for observability."""

    @abstractmethod
    def processed_count(self) -> int:
        """Number of entities successfully processed."""
        raise NotImplementedError

    @abstractmethod
    def failed_count(self) -> int:
        """Number of entities that failed processing."""
        raise NotImplementedError


class LifecycleHandler[
    Entity,
    Result: LifecycleResult,
    Category,
    TargetStatuses,
    StatusTransitions,
](ABC):
    """One lifecycle stage's filter declaration, execution, and post-processing."""

    @classmethod
    @abstractmethod
    def name(cls) -> str:
        """Stable identifier of this handler."""
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def kind(cls) -> str:
        """Entity kind for this handler (e.g. 'route', 'deployment', 'group')."""
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def category(cls) -> Category:
        """History/query category for this handler."""
        raise NotImplementedError

    @property
    @abstractmethod
    def lock_id(self) -> LockID | None:
        """Lock to acquire before execution, or None."""
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def target_statuses(cls) -> TargetStatuses:
        """Entity statuses this handler consumes."""
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def status_transitions(cls) -> StatusTransitions:
        """Per-outcome target statuses."""
        raise NotImplementedError

    @abstractmethod
    async def execute(self, entities: Sequence[Entity]) -> Result:
        """Run the stage over the fetched entities."""
        raise NotImplementedError

    @abstractmethod
    async def post_process(self, result: Result) -> None:
        """Side effects after transitions are applied."""
        raise NotImplementedError


class LifecycleEntitySource[
    Entity,
    Result: LifecycleResult,
    Category,
    TargetStatuses,
    StatusTransitions,
](ABC):
    """Fetches the entities a handler targets, reading the handler's own declaration."""

    @abstractmethod
    async def fetch(
        self,
        handler: LifecycleHandler[Entity, Result, Category, TargetStatuses, StatusTransitions],
    ) -> list[Entity]:
        """Return entities matching handler.target_statuses()/category()."""
        raise NotImplementedError

    @abstractmethod
    def extract_id(self, entity: Entity) -> UUID:
        """Return the recorder entity id for the given entity."""
        raise NotImplementedError


class LifecycleTransitionApplier[
    Entity,
    Result: LifecycleResult,
    Category,
    TargetStatuses,
    StatusTransitions,
](ABC):
    """Applies status transitions (and history) for a handler's result."""

    @abstractmethod
    async def apply(
        self,
        handler: LifecycleHandler[Entity, Result, Category, TargetStatuses, StatusTransitions],
        result: Result,
        records: Mapping[UUID, ExecutionRecord],
    ) -> None:
        """Persist transitions/history derived from the handler result and records."""
        raise NotImplementedError


class LifecycleStageRunner(ABC):
    """Type-erased stage view the coordinator dispatches; carries no entity types."""

    @property
    @abstractmethod
    def lock_id(self) -> LockID | None:
        """Lock to acquire before running, or None."""
        raise NotImplementedError

    @abstractmethod
    async def run(self) -> bool:
        """Fetch -> execute -> apply -> post_process. Returns False if nothing matched."""
        raise NotImplementedError


@dataclass(frozen=True)
class LifecycleStage[Entity, Result: LifecycleResult, Category, TargetStatuses, StatusTransitions](
    LifecycleStageRunner
):
    """A type-consistent (source, handler, applier) bundle for one lifecycle type."""

    handler: LifecycleHandler[Entity, Result, Category, TargetStatuses, StatusTransitions]
    source: LifecycleEntitySource[Entity, Result, Category, TargetStatuses, StatusTransitions]
    applier: LifecycleTransitionApplier[Entity, Result, Category, TargetStatuses, StatusTransitions]

    @property
    def lock_id(self) -> LockID | None:
        return self.handler.lock_id

    async def run(self) -> bool:
        metrics = LifecycleMetricObserver.instance()
        kind = self.handler.kind()
        handler_name = self.handler.name()
        with metrics.measure(kind, handler_name, "fetch"):
            entities = await self.source.fetch(self.handler)
        if not entities:
            return False
        ids = [self.source.extract_id(entity) for entity in entities]
        with RecorderContext[UUID].scope(handler_name, ids) as pool:
            with metrics.measure(kind, handler_name, "execute"):
                result = await self.handler.execute(entities)
            metrics.observe_processed(
                kind, handler_name, result.processed_count(), result.failed_count()
            )
            records = pool.build_all_records()
            with metrics.measure(kind, handler_name, "apply"):
                await self.applier.apply(self.handler, result, records)
        with metrics.measure(kind, handler_name, "post_process"):
            await self.handler.post_process(result)
        return True


class LifecycleNeededFlags(ABC):
    """Namespaced 'processing needed' marks backed by valkey."""

    @abstractmethod
    async def mark_needed(self, lifecycle_type: str) -> None:
        """Mark that the given lifecycle type needs processing."""
        raise NotImplementedError

    @abstractmethod
    async def load_and_delete(self, lifecycle_type: str) -> bool:
        """Atomically consume the mark; True if one existed."""
        raise NotImplementedError


@dataclass
class LifecycleTaskSpec:
    """Short/long tick spec for one lifecycle type with injected event factories."""

    lifecycle_type: str
    if_needed_event_factory: Callable[[str], AbstractAnycastEvent]
    process_event_factory: Callable[[str], AbstractAnycastEvent]
    short_interval: float | None = None
    long_interval: float = 60.0
    initial_delay: float = 30.0

    def create_if_needed_event(self) -> AbstractAnycastEvent:
        return self.if_needed_event_factory(self.lifecycle_type)

    def create_process_event(self) -> AbstractAnycastEvent:
        return self.process_event_factory(self.lifecycle_type)

    @property
    def short_task_name(self) -> str:
        return f"lifecycle_process_if_needed_{self.lifecycle_type}"

    @property
    def long_task_name(self) -> str:
        return f"lifecycle_process_{self.lifecycle_type}"
