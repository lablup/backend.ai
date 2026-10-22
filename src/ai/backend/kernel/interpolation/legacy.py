import re
from collections.abc import Mapping
from typing import Any, override

from ai.backend.kernel.interpolation.base import BaseServiceInterpolator
from ai.backend.kernel.interpolation.types import InterpolationOption

# ``${{ ... }}`` (github-style) or ``{ ... }`` (python-style) not preceded by ``$`` or ``{``,
# so shell expansions such as ``${HOME}`` stay untouched.
LEGACY_PATTERN = re.compile(
    r"""
    (\${{\s*(?P<expr1>.*?)\s*}}) |
    ((?<![${]){\s*(?P<expr2>.*?)\s*})
    """,
    re.VERBOSE,
)


class LegacyInterpolator(BaseServiceInterpolator):
    """``{var}`` and ``${{ var }}``, the syntax image service-defs are written in."""

    @override
    def pattern(self, option: InterpolationOption) -> re.Pattern[str]:
        return LEGACY_PATTERN

    @override
    def render(self, value: str, variables: Mapping[str, Any], option: InterpolationOption) -> str:
        # Pre-start action args have always gone through plain ``str.format_map``.
        return value.format_map(variables)

    @override
    def _value_error_hint(self) -> str:
        return " Literal braces (e.g. JSON like vLLM '--hf-overrides') are not supported."
