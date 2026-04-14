from dataclasses import dataclass

import pytest

from ai.backend.common.clients.prometheus import MetricPreset


@dataclass
class RenderTestCase:
    id: str
    template: str
    labels: dict[str, str]
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
                labels={"job": "test"},
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
                labels={"job": "test"},
                group_by=frozenset({"instance"}),
                window="5m",
                expected='sum(rate(my_metric{job="test"}[5m])) by (instance)',
            ),
            RenderTestCase(
                id="escapes_double_quotes_in_label_value",
                template="my_metric{{{labels}}}",
                labels={"key": 'value with "quotes"'},
                group_by=frozenset(),
                window="",
                expected='my_metric{key="value with \\"quotes\\""}',
            ),
            RenderTestCase(
                id="escapes_backslash_in_label_value",
                template="my_metric{{{labels}}}",
                labels={"path": "C:\\Users\\test"},
                group_by=frozenset(),
                window="",
                expected='my_metric{path="C:\\\\Users\\\\test"}',
            ),
            RenderTestCase(
                id="escapes_newline_in_label_value",
                template="my_metric{{{labels}}}",
                labels={"msg": "line1\nline2"},
                group_by=frozenset(),
                window="",
                expected='my_metric{msg="line1\\nline2"}',
            ),
            RenderTestCase(
                id="escapes_mixed_special_chars",
                template="my_metric{{{labels}}}",
                labels={"data": 'path\\to\\"file"\nend'},
                group_by=frozenset(),
                window="",
                expected='my_metric{data="path\\\\to\\\\\\"file\\"\\nend"}',
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
