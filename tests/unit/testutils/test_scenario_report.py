"""The scenario report lists each adapter operation under how it is built."""

from __future__ import annotations

import pathlib
import textwrap
from dataclasses import replace

import pytest

from ai.backend.testutils.scenario_report import (
    AdapterWiring,
    ComponentReport,
    Composition,
    JsonFormat,
    Line,
    MarkdownFormat,
    OperationReport,
    Report,
    ScenarioRecord,
)
from ai.backend.testutils.scenario_steps import Language, Refused, Says

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
        description=f"{summary or operation} {'is refused' if refused else 'answers'}",
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
                "Scenario: incomplete 6 / 7",
                "",
                "- built from ops (2)",
                "  - batch_load — representative success ✗ · representative refusal ✗"
                " — SCENARIO-GAP",
                "  - get — representative success ✓ · representative refusal ✓",
                "- ops + direct implementation (1)",
                "  - refresh — success present 2 · refusal absent (single_entity, single_get_ops)"
                " — SCENARIO-GAP",
                "- direct implementation (3)",
                "  - approve — success absent · refusal absent (single_field) — SCENARIO-GAP",
                "  - legacy — success absent · refusal absent (ActionProcessor) — SCENARIO-GAP",
                "  - rename — success absent · refusal present 1 (single_entity) — SCENARIO-GAP",
                "- no Action (1)",
                "  - describe — success absent · refusal absent — SCENARIO-GAP",
            ])
            in rendered
        )

    def test_the_korean_report_keeps_the_korean_words(self, report: Report) -> None:
        rendered = MarkdownFormat(Language.KOREAN).render_one(report.components[0])

        assert "시나리오: 미완 6 / 7" in rendered
        assert "- 직접 구현 (3)" in rendered
        assert "representative success" not in rendered

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

        assert "Scenario: complete" in rendered
        assert "SCENARIO-GAP" not in rendered


class TestMarkdownOperationTables:
    def test_each_operation_called_has_a_table_under_the_list(self, report: Report) -> None:
        rendered = MarkdownFormat().render_one(report.components[0])

        assert (
            "\n".join([
                "  - describe — success absent · refusal absent — SCENARIO-GAP",
                "",
                "**get**",
                "",
                "| scenario | verdict |",
                "|---|---|",
                "| [get answers](#widget-get-answered) | answered |",
                "| [get is refused](#widget-get-refused) | refused |",
                "",
                "**refresh**",
                "",
                "| scenario | verdict |",
                "|---|---|",
                "| [refresh-1 answers](#widget-refresh-1) | answered |",
                "| [refresh-2 answers](#widget-refresh-2) | answered |",
                "",
                "**rename**",
                "",
                "| scenario | verdict |",
                "|---|---|",
                "| [rename is refused](#widget-rename-refused) | refused |",
                "",
                "### get",
            ])
            in rendered
        )

    def test_successes_come_before_refusals_each_in_summary_order(
        self, manager: pathlib.Path
    ) -> None:
        report = Report.of(
            [
                _record("get", refused=True, summary="b"),
                _record("get", summary="d"),
                _record("get", refused=True, summary="a"),
                _record("get", summary="c"),
            ],
            AdapterWiring(manager),
        )

        rendered = MarkdownFormat().render_one(report.components[0])

        assert (
            "\n".join([
                "| [c answers](#widget-c) | answered |",
                "| [d answers](#widget-d) | answered |",
                "| [a is refused](#widget-a) | refused |",
                "| [b is refused](#widget-b) | refused |",
            ])
            in rendered
        )

    def test_an_operation_the_list_does_not_name_comes_last(self, manager: pathlib.Path) -> None:
        report = Report.of([_record("batch_load_fields"), _record("get")], AdapterWiring(manager))

        rendered = MarkdownFormat().render_one(report.components[0])

        assert rendered.index("**get**") < rendered.index("**batch_load_fields**")

    def test_each_link_lands_on_the_details_of_its_row(self, report: Report) -> None:
        rendered = MarkdownFormat().render_one(report.components[0])

        assert (
            "\n".join([
                '<a id="widget-get-refused"></a>',
                "",
                "#### [get-refused](/tests/scenario/bai_scenario/manager/widget/test_widget.py)"
                " — pass",
            ])
            in rendered
        )

    def test_the_details_follow_the_tables_by_operation(self, report: Report) -> None:
        rendered = MarkdownFormat().render_one(report.components[0])
        details = rendered[rendered.index("### get") :]

        order = [
            "### get",
            "#### [get-answered]",
            "#### [get-refused]",
            "### refresh",
            "#### [refresh-1]",
            "#### [refresh-2]",
            "### rename",
            "#### [rename-refused]",
        ]
        assert [details.index(one) for one in order] == sorted(details.index(one) for one in order)

    def test_a_bar_in_a_description_does_not_split_the_cell(self, manager: pathlib.Path) -> None:
        record = replace(_record("get"), description="a | b")

        rendered = MarkdownFormat().render_one(
            Report.of([record], AdapterWiring(manager)).components[0]
        )

        assert "| [a \\| b](#widget-get-answered) | answered |" in rendered


class TestBilingualReport:
    def test_a_sentence_with_english_is_written_in_that_language(
        self, manager: pathlib.Path
    ) -> None:
        record = replace(
            _record("get"), description=Says("위젯을 읽는다", english="Reads a widget")
        )
        component = Report.of([record], AdapterWiring(manager)).components[0]

        assert "Reads a widget" in MarkdownFormat().render_one(component)
        assert "위젯을 읽는다" in MarkdownFormat(Language.KOREAN).render_one(component)

    def test_a_sentence_without_english_falls_back_to_korean_in_both_reports(
        self, manager: pathlib.Path
    ) -> None:
        record = replace(_record("get"), description=Says("위젯을 읽는다"))
        component = Report.of([record], AdapterWiring(manager)).components[0]

        assert "위젯을 읽는다" in MarkdownFormat().render_one(component)
        assert "위젯을 읽는다" in MarkdownFormat(Language.KOREAN).render_one(component)

    def test_a_split_report_writes_one_file_per_language(self) -> None:
        assert list(MarkdownFormat().variants()) == ["report.md", "report.ko.md"]

    def test_the_record_keeps_both_sentences(self) -> None:
        record = replace(
            _record("get"),
            description=Says("위젯을 읽는다", english="Reads a widget"),
            when=Says("읽는다", english="reads"),
            given=(Line(says=Says("위젯이 있다", english="a widget exists")),),
        )

        again = ScenarioRecord.from_line(record.as_line())

        assert isinstance(again.description, Says)
        assert isinstance(again.when, Says)
        assert isinstance(again.given[0].says, Says)
        assert again.description.english == "Reads a widget"
        assert again.when.english == "reads"
        assert again.given[0].says.english == "a widget exists"

    def test_the_json_report_carries_both_sentences(self, manager: pathlib.Path) -> None:
        record = replace(
            _record("get"), description=Says("위젯을 읽는다", english="Reads a widget")
        )

        rendered = JsonFormat().render_one(
            Report.of([record], AdapterWiring(manager)).components[0]
        )

        assert '"korean": "위젯을 읽는다"' in rendered
        assert '"english": "Reads a widget"' in rendered


class TestComponentHeader:
    def test_a_component_without_knowledge_links_only_its_adapter(
        self, manager: pathlib.Path
    ) -> None:
        component = Report.of([_record("get")], AdapterWiring(manager)).components[0]

        rendered = MarkdownFormat().render_one(component)

        assert "what it guarantees" not in rendered
        assert "[adapter](/src/ai/backend/manager/api/adapters/widget/adapter.py)" in rendered

    def test_a_component_with_knowledge_links_it_too(self, manager: pathlib.Path) -> None:
        (manager / "api" / "adapters" / "widget" / "KNOWLEDGE.md").write_text("")
        component = Report.of([_record("get")], AdapterWiring(manager)).components[0]

        rendered = MarkdownFormat().render_one(component)

        assert (
            "[what it guarantees](/src/ai/backend/manager/api/adapters/widget/KNOWLEDGE.md)"
            in rendered
        )

    def test_the_korean_header_uses_the_korean_words(self, manager: pathlib.Path) -> None:
        (manager / "api" / "adapters" / "widget" / "KNOWLEDGE.md").write_text("")
        component = Report.of([_record("get")], AdapterWiring(manager)).components[0]

        rendered = MarkdownFormat(Language.KOREAN).render_one(component)

        assert "[무엇을 보장하는가](" in rendered
        assert "[어댑터](" in rendered


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

    def test_each_table_names_its_operation_with_its_adapter(
        self, manager: pathlib.Path, records: list[ScenarioRecord]
    ) -> None:
        rendered = MarkdownFormat().render(Report.of(records, AdapterWiring(manager)))

        assert "**WidgetAdapter.get**" in rendered
        assert "**WidgetSessionAdapter.get**" in rendered

    def test_the_report_does_not_depend_on_the_order_records_arrive_in(
        self, manager: pathlib.Path, records: list[ScenarioRecord]
    ) -> None:
        forward = Report.of(records, AdapterWiring(manager))
        backward = Report.of(list(reversed(records)), AdapterWiring(manager))

        assert MarkdownFormat().render(forward) == MarkdownFormat().render(backward)
