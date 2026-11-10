from __future__ import annotations

import asyncio
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import override

import pytest
from opentelemetry import trace
from opentelemetry.sdk.trace import ReadableSpan
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from opentelemetry.trace import StatusCode

from ai.backend.common.data.entity.types import EntityIdentifier, EntityType
from ai.backend.common.data.entity.vfolder import VFolderEntityType
from ai.backend.common.exception import PermissionDeniedError
from ai.backend.common.resilience.resilience import Resilience
from ai.backend.manager.actions.types import ActionOperationType, OperationStatus
from ai.backend.manager.actions.v2.bulk.monitor.tracing import BulkActionTracingMonitor
from ai.backend.manager.actions.v2.bulk.result import (
    BulkActionProcessResult,
    BulkActionResultMeta,
    BulkEntityResult,
)
from ai.backend.manager.actions.v2.bulk.trigger import BulkActionTriggerMeta
from ai.backend.manager.actions.v2.single_entity.base import BaseSingleEntityAction
from ai.backend.manager.actions.v2.single_entity.monitor.base import SingleEntityActionMonitor
from ai.backend.manager.actions.v2.single_entity.monitor.tracing import (
    SingleEntityActionTracingMonitor,
)
from ai.backend.manager.actions.v2.single_entity.processor import SingleEntityActionProcessor
from ai.backend.manager.actions.v2.single_entity.result import SingleEntityActionProcessResult
from ai.backend.manager.actions.v2.single_entity.trigger import SingleEntityActionTriggerMeta
from ai.backend.manager.actions.v2.single_entity.validator.base import (
    SingleEntityActionValidator,
)
from ai.backend.manager.errors.common import InternalServerError


class _StubEntityID(EntityIdentifier):
    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return VFolderEntityType()


@dataclass
class _Action(BaseSingleEntityAction):
    name: str

    @override
    def entity_id(self) -> EntityIdentifier:
        return _StubEntityID(uuid.uuid4())

    @classmethod
    @override
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET

    @classmethod
    @override
    def action_name(cls) -> str:
        return "get_vfolder"


class _Repository:
    @Resilience(policies=[]).apply()
    async def fetch(self, name: str) -> str:
        await asyncio.sleep(0)
        return name


class _SpanCapturingMonitor(SingleEntityActionMonitor):
    """Stands in for the audit log monitor, which writes to the DB in ``done``."""

    done_span_ids: list[int]

    def __init__(self) -> None:
        self.done_span_ids = []

    @override
    async def prepare(self, meta: SingleEntityActionTriggerMeta) -> None:
        return

    @override
    async def done(
        self, meta: SingleEntityActionTriggerMeta, result: SingleEntityActionProcessResult
    ) -> None:
        self.done_span_ids.append(trace.get_current_span().get_span_context().span_id)


class _DenyingValidator(SingleEntityActionValidator):
    @override
    async def validate(self, meta: SingleEntityActionTriggerMeta) -> None:
        raise PermissionDeniedError("nope")


async def _fetch(action: _Action) -> str:
    return await _Repository().fetch(action.name)


async def _fail(action: _Action) -> str:
    raise InternalServerError("broken")


def _spans_named(exporter: InMemorySpanExporter, name: str) -> list[ReadableSpan]:
    return [span for span in exporter.get_finished_spans() if span.name == name]


class TestSingleEntityActionTracing:
    async def test_success_span_parents_repository_span(
        self, span_exporter: InMemorySpanExporter
    ) -> None:
        processor = SingleEntityActionProcessor[_Action, str](
            func=_fetch, monitors=[SingleEntityActionTracingMonitor()]
        )

        await processor.run(_Action(name="a"))

        (action_span,) = _spans_named(span_exporter, "get_vfolder")
        (repository_span,) = _spans_named(span_exporter, "_Repository.fetch")
        assert action_span.status.status_code == StatusCode.UNSET
        assert action_span.attributes is not None
        assert action_span.attributes["backendai.action.status"] == "success"
        assert action_span.attributes["backendai.action.operation"] == "get"
        assert repository_span.parent is not None
        assert repository_span.parent.span_id == action_span.context.span_id
        assert trace.get_current_span().get_span_context().is_valid is False

    async def test_failure_records_error_code(self, span_exporter: InMemorySpanExporter) -> None:
        processor = SingleEntityActionProcessor[_Action, str](
            func=_fail, monitors=[SingleEntityActionTracingMonitor()]
        )

        with pytest.raises(InternalServerError):
            await processor.run(_Action(name="a"))

        (action_span,) = _spans_named(span_exporter, "get_vfolder")
        assert action_span.status.status_code == StatusCode.ERROR
        assert action_span.attributes is not None
        assert action_span.attributes["backendai.action.status"] == "error"
        assert action_span.attributes["backendai.error_code"] == str(
            InternalServerError("broken").error_code()
        )

    async def test_denied_validation_is_an_error_span(
        self, span_exporter: InMemorySpanExporter
    ) -> None:
        processor = SingleEntityActionProcessor[_Action, str](
            func=_fetch,
            monitors=[SingleEntityActionTracingMonitor()],
            validators=[_DenyingValidator()],
        )

        with pytest.raises(PermissionDeniedError):
            await processor.run(_Action(name="a"))

        (action_span,) = _spans_named(span_exporter, "get_vfolder")
        assert action_span.status.status_code == StatusCode.ERROR
        assert action_span.attributes is not None
        assert action_span.attributes["backendai.action.status"] == "denied"

    async def test_later_monitors_run_inside_action_span(
        self, span_exporter: InMemorySpanExporter
    ) -> None:
        capturing = _SpanCapturingMonitor()
        processor = SingleEntityActionProcessor[_Action, str](
            func=_fetch, monitors=[SingleEntityActionTracingMonitor(), capturing]
        )

        await processor.run(_Action(name="a"))

        (action_span,) = _spans_named(span_exporter, "get_vfolder")
        assert capturing.done_span_ids == [action_span.context.span_id]

    async def test_concurrent_runs_keep_their_own_spans(
        self, span_exporter: InMemorySpanExporter
    ) -> None:
        processor = SingleEntityActionProcessor[_Action, str](
            func=_fetch, monitors=[SingleEntityActionTracingMonitor()]
        )

        await asyncio.gather(*(processor.run(_Action(name=str(i))) for i in range(5)))

        action_span_ids = {
            span.context.span_id for span in _spans_named(span_exporter, "get_vfolder")
        }
        repository_spans = _spans_named(span_exporter, "_Repository.fetch")
        assert len(action_span_ids) == 5
        assert len(repository_spans) == 5
        parent_ids = {span.parent.span_id for span in repository_spans if span.parent is not None}
        assert parent_ids == action_span_ids

    async def test_nested_action_span_restores_the_outer_span(
        self, span_exporter: InMemorySpanExporter
    ) -> None:
        inner = SingleEntityActionProcessor[_Action, str](
            func=_fetch, monitors=[SingleEntityActionTracingMonitor()]
        )
        spans_after_inner: list[int] = []

        async def _run_inner(action: _Action) -> str:
            result = await inner.run(_Action(name="inner"))
            spans_after_inner.append(trace.get_current_span().get_span_context().span_id)
            return result

        outer = SingleEntityActionProcessor[_Action, str](
            func=_run_inner, monitors=[SingleEntityActionTracingMonitor()]
        )

        await outer.run(_Action(name="outer"))

        outer_span, inner_span = sorted(
            _spans_named(span_exporter, "get_vfolder"), key=lambda span: span.start_time or 0
        )
        assert inner_span.parent is not None
        assert inner_span.parent.span_id == outer_span.context.span_id
        assert spans_after_inner == [outer_span.context.span_id]
        assert trace.get_current_span().get_span_context().is_valid is False


def _bulk_meta() -> BulkActionTriggerMeta:
    return BulkActionTriggerMeta(
        action_id=uuid.uuid4(),
        started_at=datetime.now(UTC),
        entity_ids=[],
        operation_type=ActionOperationType.DELETE,
        action_name="bulk_delete_vfolders",
    )


def _bulk_result(entity_results: list[BulkEntityResult]) -> BulkActionProcessResult:
    now = datetime.now(UTC)
    return BulkActionProcessResult(
        meta=BulkActionResultMeta(
            action_id=uuid.uuid4(),
            entity_results=entity_results,
            started_at=now,
            ended_at=now,
            duration=timedelta(0),
        )
    )


def _entity_result(status: OperationStatus) -> BulkEntityResult:
    return BulkEntityResult(
        entity_id=_StubEntityID(uuid.uuid4()),
        status=status,
        description=str(status),
        error_code=None,
    )


class TestBulkActionTracing:
    async def test_partly_failed_run_takes_the_first_failure(
        self, span_exporter: InMemorySpanExporter
    ) -> None:
        monitor = BulkActionTracingMonitor()
        meta = _bulk_meta()

        await monitor.prepare(meta)
        await monitor.done(
            meta,
            _bulk_result([
                _entity_result(OperationStatus.SUCCESS),
                _entity_result(OperationStatus.DENIED),
                _entity_result(OperationStatus.ERROR),
            ]),
        )

        (span,) = span_exporter.get_finished_spans()
        assert span.status.status_code == StatusCode.ERROR
        assert span.attributes is not None
        assert span.attributes["backendai.action.status"] == "denied"

    async def test_run_without_results_gets_no_status(
        self, span_exporter: InMemorySpanExporter
    ) -> None:
        monitor = BulkActionTracingMonitor()
        meta = _bulk_meta()

        await monitor.prepare(meta)
        await monitor.done(meta, _bulk_result([]))

        (span,) = span_exporter.get_finished_spans()
        assert span.status.status_code == StatusCode.UNSET
        assert span.attributes is not None
        assert "backendai.action.status" not in span.attributes
