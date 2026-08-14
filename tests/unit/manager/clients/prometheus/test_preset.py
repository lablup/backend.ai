from dataclasses import dataclass

import pytest

from ai.backend.common.exception import InvalidMetricPresetTemplate
from ai.backend.manager.clients.prometheus.preset import (
    LabelMatcher,
    MetricPreset,
    PromQLTemplateRenderer,
)


@pytest.fixture
def renderer() -> PromQLTemplateRenderer:
    return PromQLTemplateRenderer()


@dataclass
class RenderTestCase:
    id: str
    template: str
    labels: dict[str, LabelMatcher]
    group_by: frozenset[str]
    window: str
    expected: str


class TestPromQLTemplateRendererRender:
    """Tests for PromQLTemplateRenderer.render()."""

    @pytest.mark.parametrize(
        "case",
        [
            RenderTestCase(
                id="empty_labels",
                template="sum(my_metric{ {{ labels }} }) by ({{ group_by }})",
                labels={},
                group_by=frozenset({"value_type"}),
                window="",
                expected="sum(my_metric{  }) by (value_type)",
            ),
            RenderTestCase(
                id="multiple_group_by_sorted",
                template="sum(my_metric{ {{ labels }} }) by ({{ group_by }})",
                labels={"job": LabelMatcher.exact("test")},
                group_by=frozenset({"value_type", "kernel_id", "session_id"}),
                window="",
                expected='sum(my_metric{ job="test" }) by (kernel_id,session_id,value_type)',
            ),
            RenderTestCase(
                id="with_window",
                template="sum(rate(my_metric{ {{ labels }} }[{{ window }}])) by ({{ group_by }})",
                labels={"job": LabelMatcher.exact("test")},
                group_by=frozenset({"instance"}),
                window="5m",
                expected='sum(rate(my_metric{ job="test" }[5m])) by (instance)',
            ),
            RenderTestCase(
                id="escapes_double_quotes_in_label_value",
                template="my_metric{ {{ labels }} }",
                labels={"key": LabelMatcher.exact('value with "quotes"')},
                group_by=frozenset(),
                window="",
                expected='my_metric{ key="value with \\"quotes\\"" }',
            ),
            RenderTestCase(
                id="escapes_backslash_in_label_value",
                template="my_metric{ {{ labels }} }",
                labels={"path": LabelMatcher.exact("C:\\Users\\test")},
                group_by=frozenset(),
                window="",
                expected='my_metric{ path="C:\\\\Users\\\\test" }',
            ),
            RenderTestCase(
                id="escapes_newline_in_label_value",
                template="my_metric{ {{ labels }} }",
                labels={"msg": LabelMatcher.exact("line1\nline2")},
                group_by=frozenset(),
                window="",
                expected='my_metric{ msg="line1\\nline2" }',
            ),
            RenderTestCase(
                id="regex_matcher",
                template="my_metric{ {{ labels }} }",
                labels={"kernel_id": LabelMatcher.regex("kernel-1|kernel-2")},
                group_by=frozenset(),
                window="",
                expected='my_metric{ kernel_id=~"kernel-1|kernel-2" }',
            ),
            # Static and injected matchers coexist in one selector.
            RenderTestCase(
                id="static_matcher_with_all_placeholders",
                template='sum by ({{ group_by }})(rate(metric{mode!="idle",{{ labels }}}[{{ window }}]))',
                labels={"job": LabelMatcher.exact("api")},
                group_by=frozenset({"instance"}),
                window="5m",
                expected='sum by (instance)(rate(metric{mode!="idle",job="api"}[5m]))',
            ),
            # Raw PromQL without placeholders — provided values are ignored,
            # single braces are literal text.
            RenderTestCase(
                id="raw_template_ignores_provided_labels",
                template='rate(node_cpu_seconds_total{mode!="idle"}[5m])',
                labels={"job": LabelMatcher.exact("api")},
                group_by=frozenset({"instance"}),
                window="5m",
                expected='rate(node_cpu_seconds_total{mode!="idle"}[5m])',
            ),
            RenderTestCase(
                id="orphan_open_brace_is_literal",
                template="metric{",
                labels={},
                group_by=frozenset(),
                window="",
                expected="metric{",
            ),
        ],
        ids=lambda c: c.id,
    )
    async def test_render(self, renderer: PromQLTemplateRenderer, case: RenderTestCase) -> None:
        preset = MetricPreset(
            template=case.template,
            labels=case.labels,
            group_by=case.group_by,
            window=case.window,
        )

        result = renderer.render(preset)

        assert result == case.expected

    @pytest.mark.parametrize(
        "template",
        [
            pytest.param("sum(metric{{{labels}}}) by ({group_by})", id="legacy_triple_brace"),
            pytest.param("metric{ {{ unknown_var }} }", id="unknown_variable"),
        ],
    )
    async def test_render_raises(self, renderer: PromQLTemplateRenderer, template: str) -> None:
        preset = MetricPreset(template=template)

        with pytest.raises(InvalidMetricPresetTemplate):
            renderer.render(preset)


class TestPromQLTemplateRendererValidate:
    """Tests for PromQLTemplateRenderer.validate() called from the service layer."""

    @pytest.mark.parametrize(
        "template",
        [
            pytest.param(
                'rate(node_cpu_seconds_total{mode!="idle"}[5m])',
                id="raw_promql",
            ),
            pytest.param(
                'count(metric{a="1",b=~"x|y"})',
                id="multiple_matchers",
            ),
            pytest.param(
                "sum by ({{ group_by }})(metric{ {{ labels }} }[{{ window }}])",
                id="jinja_placeholders",
            ),
            pytest.param(
                'sum by ({{ group_by }})(metric{mode!="idle",{{ labels }}})',
                id="static_and_dynamic_labels",
            ),
        ],
    )
    def test_accepts_valid_template(self, renderer: PromQLTemplateRenderer, template: str) -> None:
        renderer.validate(template)  # does not raise

    @pytest.mark.parametrize(
        "template",
        [
            pytest.param("sum(metric{labels})", id="bare_placeholder"),
            pytest.param("sum by ({group_by})(metric[{window}])", id="bare_group_by_and_window"),
            pytest.param("sum(metric{{{labels}}})", id="triple_brace"),
        ],
    )
    def test_rejects_legacy_syntax(self, renderer: PromQLTemplateRenderer, template: str) -> None:
        with pytest.raises(InvalidMetricPresetTemplate, match="Legacy"):
            renderer.validate(template)

    @pytest.mark.parametrize(
        "template",
        [
            pytest.param('rate(metric{mode!="idle"}[$__rate_interval])', id="grafana_builtin"),
            pytest.param('metric{job="$service"}', id="dollar_identifier"),
            pytest.param('metric{region="${region}"}', id="braced_dollar_var"),
        ],
    )
    def test_rejects_unsupported_template_variables(
        self, renderer: PromQLTemplateRenderer, template: str
    ) -> None:
        with pytest.raises(InvalidMetricPresetTemplate, match="Unsupported"):
            renderer.validate(template)

    @pytest.mark.parametrize(
        "template",
        [
            pytest.param("{% if labels %}metric{% endif %}", id="statement_block"),
            pytest.param("metric{ {{ unknown_var }} }", id="unknown_variable"),
            pytest.param("metric{ {{ labels | upper }} }", id="filter"),
            pytest.param("metric{ {{ labels.attr }} }", id="attribute_access"),
            pytest.param("   ", id="blank"),
        ],
    )
    def test_rejects_disallowed_constructs(
        self, renderer: PromQLTemplateRenderer, template: str
    ) -> None:
        with pytest.raises(InvalidMetricPresetTemplate):
            renderer.validate(template)
