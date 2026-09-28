"""The scenario report lists each adapter operation under how it is built."""

from __future__ import annotations

import pathlib
import textwrap

import pytest

from ai.backend.testutils.scenario_report import (
    AdapterWiring,
    ComponentReport,
    Composition,
    Line,
    MarkdownFormat,
    OperationReport,
    Report,
    ScenarioRecord,
)
from ai.backend.testutils.scenario_steps import Refused

_PROCESSORS = """
class WidgetRevisionProcessors:
    def __init__(self, group):
        self.approve = group.single_field(ApproveAction, service.approve)


class WidgetProcessors:
    revision: WidgetRevisionProcessors

    def __init__(self, group, revision, service):
        self.revision = revision
        self.get = group.single_get_ops(GetWidgetAction)
        self.bulk_get = group.partial_bulk_get_ops(BulkGetWidgetsAction)
        self.lookup = group.public_lookup_ops(LookupWidgetAction)
        self.rename = group.single_entity(RenameWidgetAction, service.rename)
        self.legacy = ActionProcessor(service.legacy)
"""

_ADAPTER = """
class WidgetAdapter(BaseAdapter):
    def __init__(self, widget: WidgetProcessors | None) -> None:
        self._widget = widget

    async def get(self, widget_id):
        return await self._widget.get.run(GetWidgetAction(widget_id))

    async def rename(self, name, new_name):
        widget = await self._widget.lookup.run(LookupWidgetAction(name))
        return await self._widget.rename.run(RenameWidgetAction(widget, new_name))

    async def refresh(self, widget_id):
        await self._read(widget_id)
        return await self._widget.rename.run(RenameWidgetAction(widget_id, None))

    async def batch_load(self, ids):
        return await self.batch_load_fields(self._widget.bulk_get, ids)

    async def approve(self, revision_id):
        return await self._widget.revision.approve.run(ApproveAction(revision_id))

    async def legacy(self):
        return await self._widget.legacy.wait_for_complete(LegacyAction())

    async def describe(self):
        return "a widget"

    async def _read(self, widget_id):
        return await self._widget.get.run(GetWidgetAction(widget_id))
"""

_SESSION_ADAPTER = """
class WidgetSessionAdapter(BaseAdapter):
    def __init__(self, widget: WidgetProcessors) -> None:
        self._widget = widget

    async def get(self, widget_id):
        return await self._widget.rename.run(RenameWidgetAction(widget_id, None))
"""

_OFFERS = (
    "approve",
    "batch_load",
    "batch_load_fields",
    "describe",
    "get",
    "legacy",
    "refresh",
    "rename",
)


@pytest.fixture
def manager(tmp_path: pathlib.Path) -> pathlib.Path:
    (tmp_path / "services" / "widget").mkdir(parents=True)
    (tmp_path / "services" / "widget" / "processors.py").write_text(textwrap.dedent(_PROCESSORS))
    (tmp_path / "api" / "adapters" / "widget").mkdir(parents=True)
    (tmp_path / "api" / "adapters" / "widget" / "adapter.py").write_text(textwrap.dedent(_ADAPTER))
    (tmp_path / "api" / "adapters" / "widget_session").mkdir(parents=True)
    (tmp_path / "api" / "adapters" / "widget_session" / "adapter.py").write_text(
        textwrap.dedent(_SESSION_ADAPTER)
    )
    return tmp_path


def _record(
    operation: str,
    *,
    refused: bool = False,
    summary: str = "",
    adapter: str = "WidgetAdapter",
) -> ScenarioRecord:
    seen = (Line(says=f"{Refused.PREFIX}NotEnoughPermission"),) if refused else (Line("id = 1"),)
    return ScenarioRecord(
        summary=summary or f"{operation}-{'refused' if refused else 'answered'}",
        description="",
        actor="",
        caller="",
        operation=operation,
        when="",
        then="",
        module="bai_scenario.manager.widget.test_widget",
        outcome="passed",
        adapter=adapter,
        seen=seen,
        offers=_OFFERS,
    )


@pytest.fixture
def report(manager: pathlib.Path) -> Report:
    return Report.of(
        [
            _record("get"),
            _record("get", refused=True),
            _record("refresh", summary="refresh-1"),
            _record("refresh", summary="refresh-2"),
            _record("rename", refused=True),
        ],
        AdapterWiring(manager),
    )


class TestAdapterWiring:
    def test_an_operation_running_only_ops_processors_is_built_from_ops(
        self, manager: pathlib.Path
    ) -> None:
        built = AdapterWiring(manager).of("widget", "WidgetAdapter")

        assert built["get"].composition is Composition.OPS
        assert built["batch_load"].composition is Composition.OPS

    def test_a_lookup_does_not_decide_the_composition(self, manager: pathlib.Path) -> None:
        built = AdapterWiring(manager).of("widget", "WidgetAdapter")

        assert built["rename"].composition is Composition.CUSTOM
        assert built["rename"].group_methods == ("single_entity",)

    def test_a_private_helper_is_followed(self, manager: pathlib.Path) -> None:
        built = AdapterWiring(manager).of("widget", "WidgetAdapter")

        assert built["refresh"].composition is Composition.MIXED
        assert built["refresh"].group_methods == ("single_entity", "single_get_ops")

    def test_a_nested_processors_field_is_followed(self, manager: pathlib.Path) -> None:
        built = AdapterWiring(manager).of("widget", "WidgetAdapter")

        assert built["approve"].group_methods == ("single_field",)
        assert built["legacy"].group_methods == ("ActionProcessor",)
        assert built["legacy"].composition is Composition.CUSTOM

    def test_an_operation_running_no_processor_has_no_action(self, manager: pathlib.Path) -> None:
        built = AdapterWiring(manager).of("widget", "WidgetAdapter")

        assert built["describe"].composition is Composition.NO_ACTION

    def test_an_operation_the_class_does_not_define_is_absent(self, manager: pathlib.Path) -> None:
        built = AdapterWiring(manager).of("widget", "WidgetAdapter")

        assert "batch_load_fields" not in built
        assert "_read" not in built

    def test_an_adapter_class_missing_from_the_source_is_refused(
        self, manager: pathlib.Path
    ) -> None:
        with pytest.raises(LookupError):
            AdapterWiring(manager).of("widget", "GadgetAdapter")


class TestMarkdownOperations:
    def test_each_operation_is_listed_under_how_it_is_built(self, report: Report) -> None:
        rendered = MarkdownFormat().render_one(report.components[0])

        assert (
            "\n".join([
                "시나리오: 미완 6 / 7",
                "",
                "- ops 로 구성 (2)",
                "  - batch_load — 대표 성공 ✗ · 대표 실패 ✗ — SCENARIO-GAP",
                "  - get — 대표 성공 ✓ · 대표 실패 ✓",
                "- ops + 직접 구현 (1)",
                "  - refresh — 성공 있음 2 · 실패 없음 (single_entity, single_get_ops) — SCENARIO-GAP",
                "- 직접 구현 (3)",
                "  - approve — 성공 없음 · 실패 없음 (single_field) — SCENARIO-GAP",
                "  - legacy — 성공 없음 · 실패 없음 (ActionProcessor) — SCENARIO-GAP",
                "  - rename — 성공 없음 · 실패 있음 1 (single_entity) — SCENARIO-GAP",
                "- Action 없음 (1)",
                "  - describe — 성공 없음 · 실패 없음 — SCENARIO-GAP",
            ])
            in rendered
        )

    def test_an_operation_with_no_action_needs_only_a_success_row(
        self, manager: pathlib.Path
    ) -> None:
        report = Report.of([_record("describe")], AdapterWiring(manager))

        assert "describe" not in report.components[0].gaps

    def test_a_component_with_every_operation_covered_is_complete(self) -> None:
        component = ComponentReport(
            component="widget",
            adapter="WidgetAdapter",
            behaviours=(),
            operations=(
                OperationReport("get", Composition.OPS, ("single_get_ops",), 1, 1),
                OperationReport("describe", Composition.NO_ACTION, (), 1, 0),
            ),
        )

        rendered = MarkdownFormat().render_one(component)

        assert "시나리오: 완성" in rendered
        assert "SCENARIO-GAP" not in rendered


class TestSeveralAdapters:
    @pytest.fixture
    def records(self) -> list[ScenarioRecord]:
        return [
            _record("get", adapter="WidgetSessionAdapter", summary="session-get"),
            _record("get"),
            _record("get", refused=True),
        ]

    def test_each_adapter_is_named_beside_its_operations(
        self, manager: pathlib.Path, records: list[ScenarioRecord]
    ) -> None:
        operations = {
            one.operation: one
            for one in Report.of(records, AdapterWiring(manager)).components[0].operations
        }

        assert operations["WidgetAdapter.get"].refused == 1
        assert operations["WidgetSessionAdapter.get"].succeeding == 1
        assert operations["WidgetSessionAdapter.get"].refused == 0

    def test_the_report_does_not_depend_on_the_order_records_arrive_in(
        self, manager: pathlib.Path, records: list[ScenarioRecord]
    ) -> None:
        forward = Report.of(records, AdapterWiring(manager))
        backward = Report.of(list(reversed(records)), AdapterWiring(manager))

        assert MarkdownFormat().render(forward) == MarkdownFormat().render(backward)
