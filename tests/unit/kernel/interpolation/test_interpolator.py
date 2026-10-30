from collections.abc import Sequence

import pytest

from ai.backend.kernel.exception import InvalidServiceDefinition
from ai.backend.kernel.interpolation.interpolator import LEGACY_DELIMITERS, ServiceInterpolator
from ai.backend.kernel.interpolation.types import InterpolationDelimiter

_LEGACY = LEGACY_DELIMITERS
_JINJA: list[InterpolationDelimiter] = [{"start": "{{", "end": "}}"}]
_JINJA_AND_ERB: list[InterpolationDelimiter] = [
    {"start": "{{", "end": "}}"},
    {"start": "<%", "end": "%>"},
]
_VARIABLES = {"host": "99.99.99.99", "ports": [11001, 11002], "port": "8000"}


class TestServiceInterpolator:
    @pytest.mark.parametrize(
        ("delimiters", "part", "expected"),
        [
            pytest.param(
                _LEGACY,
                'echo "host = {host}, port = {ports[1]}"',
                'echo "host = 99.99.99.99, port = 11002"',
                id="legacy-python-style",
            ),
            pytest.param(
                _LEGACY,
                'echo "host = ${{ host }}, port = ${{ ports[1] }}"',
                'echo "host = 99.99.99.99, port = 11002"',
                id="legacy-github-style",
            ),
            pytest.param(
                _LEGACY,
                'echo "kernel_id = $BACKENDAI_KERNEL_ID"',
                'echo "kernel_id = $BACKENDAI_KERNEL_ID"',
                id="legacy-skips-shell-envvar",
            ),
            pytest.param(
                _LEGACY,
                'echo "kernel_id = ${BACKENDAI_KERNEL_ID/aaa/${magic}}"',
                'echo "kernel_id = ${BACKENDAI_KERNEL_ID/aaa/${magic}}"',
                id="legacy-skips-braced-shell-envvar",
            ),
            pytest.param(
                _LEGACY,
                'echo "host = ${{ host }}, kernel_id = ${BACKENDAI_KERNEL_ID/aaa/${magic}}, port = {ports[0]}"',
                'echo "host = 99.99.99.99, kernel_id = ${BACKENDAI_KERNEL_ID/aaa/${magic}}, port = 11001"',
                id="legacy-mixed",
            ),
            pytest.param(
                _JINJA,
                """serve --port {{ port }} --hf-overrides '{"method":"mtp"}'""",
                """serve --port 8000 --hf-overrides '{"method":"mtp"}'""",
                id="delimiter-json-stays-literal",
            ),
            pytest.param(
                _JINJA,
                "{{port}} {{ port }} {port}",
                "8000 8000 {port}",
                id="delimiter-spacing-and-single-braces",
            ),
            pytest.param(
                _JINJA_AND_ERB,
                "{{ port }} <% host %> {port}",
                "8000 99.99.99.99 {port}",
                id="delimiter-multiple",
            ),
        ],
    )
    def test_apply(
        self, delimiters: Sequence[InterpolationDelimiter], part: str, expected: str
    ) -> None:
        assert ServiceInterpolator(_VARIABLES, delimiters).apply([part]) == [expected]

    @pytest.mark.parametrize(
        ("delimiters", "mentions_literal_braces"),
        [
            pytest.param(_LEGACY, True, id="legacy"),
            pytest.param(_JINJA, False, id="delimiter"),
        ],
    )
    def test_malformed_expression(
        self, delimiters: Sequence[InterpolationDelimiter], mentions_literal_braces: bool
    ) -> None:
        with pytest.raises(InvalidServiceDefinition) as exc_info:
            ServiceInterpolator(_VARIABLES, delimiters).apply(["{{ ports[0 }}"])

        assert ("Literal braces" in str(exc_info.value)) is mentions_literal_braces

    def test_requires_a_delimiter(self) -> None:
        with pytest.raises(InvalidServiceDefinition):
            ServiceInterpolator(_VARIABLES, [])
