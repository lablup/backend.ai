import pytest

from ai.backend.kernel.exception import InvalidServiceDefinition
from ai.backend.kernel.interpolation.delimiter import DelimiterInterpolator
from ai.backend.kernel.interpolation.types import InterpolationOption

_JINJA: InterpolationOption = {"mode": "delimiter", "delimiter": {"start": "{{", "end": "}}"}}


class TestDelimiterInterpolator:
    @pytest.fixture
    def interpolator(self) -> DelimiterInterpolator:
        return DelimiterInterpolator()

    @pytest.mark.parametrize(
        ("part", "expected"),
        [
            pytest.param(
                """serve --port {{ port }} --hf-overrides '{"method":"mtp"}'""",
                """serve --port 8000 --hf-overrides '{"method":"mtp"}'""",
                id="json-stays-literal",
            ),
            pytest.param(
                "{{port}} {{ port }} {port}", "8000 8000 {port}", id="spacing-and-single-braces"
            ),
        ],
    )
    def test_fills_only_delimited_expressions(
        self, interpolator: DelimiterInterpolator, part: str, expected: str
    ) -> None:
        assert interpolator.apply([part], {"port": "8000"}, _JINJA) == [expected]

    def test_malformed_expression_error_does_not_mention_literal_braces(
        self, interpolator: DelimiterInterpolator
    ) -> None:
        with pytest.raises(InvalidServiceDefinition) as exc_info:
            interpolator.apply(["{{ ports[0 }}"], {"ports": [8000]}, _JINJA)

        assert "Literal braces" not in str(exc_info.value)
