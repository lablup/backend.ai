from __future__ import annotations

import logging
from collections.abc import Sequence
from datetime import timedelta
from typing import override

from ai.backend.common.data.idle_checker.types import UtilizationSpec
from ai.backend.common.identifier.prometheus_query_preset import PrometheusQueryPresetID
from ai.backend.common.types import SessionId
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.repositories.metric.repository import MetricRepository
from ai.backend.manager.sokovan.idle_check.checkers.base import (
    CheckerAssignment,
    IdleActivityDecision,
    IdleChecker,
    IdleCheckerContext,
)

log = BraceStyleAdapter(logging.getLogger(__name__))


class UtilizationChecker(IdleChecker):
    """Judge session utilization from agent-emitted Prometheus metrics."""

    _metric_repository: MetricRepository

    def __init__(self, metric_repository: MetricRepository) -> None:
        self._metric_repository = metric_repository

    @override
    async def judge(
        self,
        assignments: Sequence[CheckerAssignment],
        *,
        context: IdleCheckerContext,
    ) -> Sequence[IdleActivityDecision]:
        # Unknown sessions are ignored because their utilization status cannot be determined.
        valid_assignments: list[tuple[CheckerAssignment, UtilizationSpec]] = []
        session_ids_by_preset: dict[PrometheusQueryPresetID, list[SessionId]] = {}
        for assignment in assignments:
            spec = assignment.definition.spec.utilization
            if spec is None:
                log.error(
                    "Utilization checker has mismatched spec type: checker_id={} spec_type={}",
                    assignment.definition.checker_id,
                    assignment.definition.spec.type,
                )
                continue
            valid_assignments.append((assignment, spec))
            session_ids = session_ids_by_preset.setdefault(spec.threshold.preset_id, [])
            for session in assignment.sessions:
                session_ids.append(session.session_id)
        if not session_ids_by_preset:
            return []

        values_by_preset = await self._metric_repository.query_session_utilization_metrics(
            session_ids_by_preset,
            evaluation_time=context.current_time,
        )
        decisions: list[IdleActivityDecision] = []
        for assignment, spec in valid_assignments:
            threshold = spec.threshold
            values = values_by_preset.get(threshold.preset_id, {})
            for session in assignment.sessions:
                value = values.get(session.session_id)
                if value is None:
                    continue
                is_active = value >= threshold.threshold
                refreshed_expire_at = context.current_time + timedelta(
                    seconds=spec.max_underutilized_duration_seconds
                )
                if is_active:
                    expire_at = refreshed_expire_at
                else:
                    expire_at = (
                        session.expire_at if session.expire_at is not None else refreshed_expire_at
                    )
                decisions.append(
                    IdleActivityDecision(
                        checker_id=assignment.definition.checker_id,
                        session_id=session.session_id,
                        expire_at=expire_at,
                        is_active=is_active,
                        message=(
                            "Utilization check: "
                            f"max_underutilized_duration_seconds="
                            f"{spec.max_underutilized_duration_seconds}, "
                            f"metric=[preset_id={threshold.preset_id}, "
                            f"value={value:f}/{threshold.threshold:f}]"
                        ),
                    )
                )
        return decisions
