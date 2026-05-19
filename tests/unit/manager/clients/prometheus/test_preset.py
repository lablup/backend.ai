from dataclasses import dataclass

import pytest

from ai.backend.common.dto.manager.v2.prometheus_query_preset.validators import (
    validate_query_template,
)
from ai.backend.common.exception import InvalidMetricPresetTemplate
from ai.backend.manager.clients.prometheus import (
    LabelMatcher,
    MetricPreset,
)


@dataclass
class RenderTestCase:
    id: str
    template: str
    labels: dict[str, LabelMatcher]
    group_by: frozenset[str]
    window: str
    expected: str


class TestMetricPresetRender:
    """Tests for MetricPreset.render() method."""

    @pytest.mark.parametrize(
        "case",
        [
            RenderTestCase(
                id="empty_labels",
                template="sum(my_metric{{{labels}}}) by ({group_by})",
                labels={},
                group_by=frozenset({"value_type"}),
                window="",
                expected="sum(my_metric{}) by (value_type)",
            ),
            RenderTestCase(
                id="multiple_group_by_sorted",
                template="sum(my_metric{{{labels}}}) by ({group_by})",
                labels={"job": LabelMatcher.exact("test")},
                group_by=frozenset({"value_type", "kernel_id", "session_id"}),
                window="",
                expected='sum(my_metric{job="test"}) by (kernel_id,session_id,value_type)',
            ),
            RenderTestCase(
                id="group_by_deduplicated",
                template="sum(my_metric{{{labels}}}) by ({group_by})",
                labels={},
                group_by=frozenset([
                    "a",
                    "b",
                    "a",
                ]),  # list allows duplicates, frozenset deduplicates
                window="",
                expected="sum(my_metric{}) by (a,b)",
            ),
            RenderTestCase(
                id="with_window",
                template="sum(rate(my_metric{{{labels}}}[{window}])) by ({group_by})",
                labels={"job": LabelMatcher.exact("test")},
                group_by=frozenset({"instance"}),
                window="5m",
                expected='sum(rate(my_metric{job="test"}[5m])) by (instance)',
            ),
            RenderTestCase(
                id="escapes_double_quotes_in_label_value",
                template="my_metric{{{labels}}}",
                labels={"key": LabelMatcher.exact('value with "quotes"')},
                group_by=frozenset(),
                window="",
                expected='my_metric{key="value with \\"quotes\\""}',
            ),
            RenderTestCase(
                id="escapes_backslash_in_label_value",
                template="my_metric{{{labels}}}",
                labels={"path": LabelMatcher.exact("C:\\Users\\test")},
                group_by=frozenset(),
                window="",
                expected='my_metric{path="C:\\\\Users\\\\test"}',
            ),
            RenderTestCase(
                id="escapes_newline_in_label_value",
                template="my_metric{{{labels}}}",
                labels={"msg": LabelMatcher.exact("line1\nline2")},
                group_by=frozenset(),
                window="",
                expected='my_metric{msg="line1\\nline2"}',
            ),
            RenderTestCase(
                id="escapes_mixed_special_chars",
                template="my_metric{{{labels}}}",
                labels={"data": LabelMatcher.exact('path\\to\\"file"\nend')},
                group_by=frozenset(),
                window="",
                expected='my_metric{data="path\\\\to\\\\\\"file\\"\\nend"}',
            ),
            RenderTestCase(
                id="regex_matcher",
                template="my_metric{{{labels}}}",
                labels={"kernel_id": LabelMatcher.regex("kernel-1|kernel-2")},
                group_by=frozenset(),
                window="",
                expected='my_metric{kernel_id=~"kernel-1|kernel-2"}',
            ),
            # Regression: original bug — `!=` in label matcher was parsed as
            # str.format conversion specifier and raised ValueError.
            RenderTestCase(
                id="raw_label_matcher_passes_through",
                template='rate(node_cpu_seconds_total{mode!="idle"}[5m])',
                labels={},
                group_by=frozenset(),
                window="",
                expected='rate(node_cpu_seconds_total{mode!="idle"}[5m])',
            ),
            # Raw matcher coexists with all placeholders + label injection.
            RenderTestCase(
                id="raw_matcher_with_all_placeholders",
                template='sum by ({group_by})(rate(metric{mode!="idle"}{{{labels}}}[{window}]))',
                labels={"job": LabelMatcher.exact("api")},
                group_by=frozenset({"instance"}),
                window="5m",
                expected='sum by (instance)(rate(metric{mode!="idle"}{job="api"}[5m]))',
            ),
            # Grafana paste with no {labels} placeholder — provided labels must
            # be silently ignored, raw matcher must survive.
            RenderTestCase(
                id="raw_template_ignores_provided_labels",
                template='rate(node_cpu_seconds_total{mode!="idle"}[5m])',
                labels={"job": LabelMatcher.exact("api")},
                group_by=frozenset({"instance"}),
                window="5m",
                expected='rate(node_cpu_seconds_total{mode!="idle"}[5m])',
            ),
            # Bare `{labels}` (single-brace) auto-wraps into PromQL `{value}`.
            RenderTestCase(
                id="bare_labels_placeholder_auto_wraps",
                template='sum by ({group_by})(rate(metric{mode!="idle"}{labels}[{window}]))',
                labels={"job": LabelMatcher.exact("api")},
                group_by=frozenset({"instance"}),
                window="5m",
                expected='sum by (instance)(rate(metric{mode!="idle"}{job="api"}[5m]))',
            ),
            RenderTestCase(
                id="bare_labels_with_empty_labels",
                template="metric{labels}",
                labels={},
                group_by=frozenset(),
                window="",
                expected="metric{}",
            ),
            # User pre-escaped a raw matcher with `{{...}}` — must not be re-escaped.
            RenderTestCase(
                id="user_escaped_double_brace_matcher",
                template='metric{{job="api"}}',
                labels={},
                group_by=frozenset(),
                window="",
                expected='metric{job="api"}',
            ),
            RenderTestCase(
                id="user_escaped_empty_braces",
                template="metric{{}}",
                labels={},
                group_by=frozenset(),
                window="",
                expected="metric{}",
            ),
        ],
        ids=lambda c: c.id,
    )
    async def test_render(self, case: RenderTestCase) -> None:
        preset = MetricPreset(
            template=case.template,
            labels=case.labels,
            group_by=case.group_by,
            window=case.window,
        )

        result = preset.render()

        assert result == case.expected

    @pytest.mark.parametrize(
        "template",
        [
            pytest.param("metric}", id="orphan_close_brace"),
            pytest.param("metric{", id="orphan_open_brace"),
            pytest.param("metric{a{b}c}", id="nested_braces"),
        ],
    )
    async def test_render_raises_on_malformed_template(self, template: str) -> None:
        preset = MetricPreset(template=template)

        with pytest.raises(InvalidMetricPresetTemplate):
            preset.render()


class TestValidateQueryTemplate:
    """Tests for validate_query_template() called from Pydantic field validators."""

    @pytest.mark.parametrize(
        "template",
        [
            pytest.param(
                'rate(node_cpu_seconds_total{mode!="idle"}[5m])',
                id="raw_promql",
            ),
            pytest.param(
                "sum by ({group_by})(metric{{{labels}}}[{window}])",
                id="with_placeholders",
            ),
            pytest.param(
                'count(metric{a="1",b=~"x|y"})',
                id="multiple_matchers",
            ),
        ],
    )
    def test_accepts_valid_template(self, template: str) -> None:
        assert validate_query_template(template) == template

    @pytest.mark.parametrize(
        "template",
        [
            pytest.param('rate(metric{mode!="idle"}[$__rate_interval])', id="grafana_builtin"),
            pytest.param('metric{job="$service"}', id="dollar_identifier"),
            pytest.param('metric{region="${region}"}', id="braced_dollar_var"),
        ],
    )
    def test_rejects_unsupported_template_variables(self, template: str) -> None:
        with pytest.raises(InvalidMetricPresetTemplate, match="Unsupported"):
            validate_query_template(template)

    @pytest.mark.parametrize(
        "template",
        [
            pytest.param("metric}", id="orphan_close_brace"),
            pytest.param("metric{", id="orphan_open_brace"),
            pytest.param("metric{a{b}c}", id="nested_braces"),
        ],
    )
    def test_rejects_malformed_template(self, template: str) -> None:
        with pytest.raises(InvalidMetricPresetTemplate):
            validate_query_template(template)
