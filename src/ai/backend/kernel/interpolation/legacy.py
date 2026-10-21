import re
from collections.abc import Mapping
from typing import Any, Self, override

from ai.backend.kernel.interpolation.base import AbstractServiceInterpolator
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


class LegacyInterpolator(AbstractServiceInterpolator):
    """``{var}`` and ``${{ var }}``, the syntax image service-defs are written in."""

    @override
    @classmethod
    def from_option(cls, variables: Mapping[str, Any], option: InterpolationOption) -> Self:
        return cls(variables)

    @property
    @override
    def pattern(self) -> re.Pattern[str]:
        return LEGACY_PATTERN

    @override
    def render(self, value: str) -> str:
        # Pre-start action args have always gone through plain ``str.format_map``.
        return value.format_map(self._variables)
