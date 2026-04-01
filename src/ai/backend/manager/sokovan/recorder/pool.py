from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID

from .recorder import TransitionRecorder
from .types import (
    ExecutionRecord,
    PhaseRecord,
    RecordBuildData,
    StepRecord,
    StepStatus,
)


@dataclass
class _SharedPhaseContext[EntityIdT: UUID]:
    """Internal context for tracking an in-progress shared phase."""

    name: str
    started_at: datetime
    success_detail: str | None
    entity_ids: set[EntityIdT] | None = None  # None means all entities
    steps: list[StepRecord] = field(default_factory=list)
    failed: bool = False


@dataclass
class _SharedPhaseRecord[EntityIdT: UUID]:
    """Internal record for a shared phase with entity filtering info."""

    phase: PhaseRecord
    entity_ids: set[EntityIdT] | None  # None means all entities


class RecordPool[EntityIdT: UUID]:
    """Storage for all entity execution records within a scope.

    This class holds the operation metadata, recorders for each entity,
    and shared phases that apply to all or specific entities.

    Records are built when scope exits by merging shared phases with
    entity-specific phases, sorted by started_at timestamp.
    """

    def __init__(
        self,
        operation: str,
        started_at: datetime,
        entity_ids: Sequence[EntityIdT],
    ) -> None:
        self.operation = operation
        self.started_at = started_at
        self.records: dict[EntityIdT, ExecutionRecord] = {}
        self._recorders: dict[EntityIdT, TransitionRecorder[EntityIdT]] = {}
        self._shared_phases: list[_SharedPhaseRecord[EntityIdT]] = []
        self._current_shared_phase: _SharedPhaseContext[EntityIdT] | None = None
        self._built = False

        # Create recorders for all entity IDs upfront
        for entity_id in entity_ids:
            self._recorders[entity_id] = TransitionRecorder(
                entity_id=entity_id,
                started_at=started_at,
            )

    def recorder(self, entity_id: EntityIdT) -> TransitionRecorder[EntityIdT]:
        """Get the recorder for a specific entity.

        Args:
            entity_id: The entity ID to get the recorder for.

        Returns:
            The TransitionRecorder instance for the entity.

        Raises:
            KeyError: If the entity_id was not in the initial entity_ids.
        """
        return self._recorders[entity_id]

    def _finalize_shared_phase(self, phase_ctx: _SharedPhaseContext[EntityIdT]) -> None:
        """Finalize and record a completed shared phase."""
        ended_at = datetime.now(UTC)

        if phase_ctx.failed:
            status = StepStatus.FAILED
            detail = None
        else:
            status = StepStatus.SUCCESS
            detail = phase_ctx.success_detail

        phase_record = PhaseRecord(
            name=phase_ctx.name,
            status=status,
            started_at=phase_ctx.started_at,
            ended_at=ended_at,
            detail=detail,
            steps=phase_ctx.steps,
        )
        self._shared_phases.append(
            _SharedPhaseRecord(phase=phase_record, entity_ids=phase_ctx.entity_ids)
        )

    def _get_shared_phases_for_entity(self, entity_id: EntityIdT) -> list[PhaseRecord]:
        """Get shared phases applicable to a specific entity."""
        return [
            sp.phase
            for sp in self._shared_phases
            if sp.entity_ids is None or entity_id in sp.entity_ids
        ]

    def build_all_records(self) -> Mapping[EntityIdT, ExecutionRecord]:
        """Build and return all execution records.

        Call this explicitly when you need records within a scope.
        Subsequent calls return cached results.
        """
        if not self._built:
            self._built = True
            ended_at = datetime.now(UTC)
            for entity_id, recorder in self._recorders.items():
                entity_shared_phases = self._get_shared_phases_for_entity(entity_id)
                build_data = RecordBuildData(
                    started_at=self.started_at,
                    ended_at=ended_at,
                    shared_phases=entity_shared_phases,
                )
                self.records[entity_id] = recorder.build_execution_record(build_data)
        return dict(self.records)

    def get_record(self, entity_id: EntityIdT) -> ExecutionRecord | None:
        """Get the execution record for an entity."""
        return self.records.get(entity_id)

    def get_all_records(self) -> dict[EntityIdT, ExecutionRecord]:
        """Get all execution records."""
        return dict(self.records)
