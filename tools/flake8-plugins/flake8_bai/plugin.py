import ast
from argparse import Namespace
from collections.abc import Iterator
from typing import Any

from flake8_bai.baseline import Baseline
from flake8_bai.rules.action_frozen import ActionFrozenRule
from flake8_bai.rules.action_pair import ActionPairRule
from flake8_bai.rules.base import Rule, SourcePath, Violation
from flake8_bai.rules.data_frozen import DataFrozenRule
from flake8_bai.rules.init_import import InitImportRule


class Plugin:
    """flake8 entry point (`[flake8:local-plugins]` in `.flake8`)."""

    name = "flake8-bai"
    version = "0.1.0"
    rule_types: tuple[type[Rule], ...] = (
        InitImportRule,
        DataFrozenRule,
        ActionFrozenRule,
        ActionPairRule,
    )
    baseline: Baseline = Baseline.empty()

    _tree: ast.Module
    _filename: str

    def __init__(self, tree: ast.Module, filename: str) -> None:
        self._tree = tree
        self._filename = filename

    @classmethod
    def add_options(cls, option_manager: Any) -> None:
        option_manager.add_option(
            "--bai-baseline",
            default="",
            parse_from_config=True,
            help="Resource in flake8_bai of the violations allowed per file",
        )

    @classmethod
    def parse_options(cls, options: Namespace) -> None:
        cls.baseline = (
            Baseline.load(options.bai_baseline) if options.bai_baseline else Baseline.empty()
        )

    def run(self) -> Iterator[tuple[int, int, str, type["Plugin"]]]:
        for violation in self.violations():
            if self.baseline.allows(self._filename, violation.code.code):
                continue
            message = f"{violation.code.code} {violation.code.message}"
            yield violation.line, violation.col, message, type(self)

    def violations(self) -> Iterator[Violation]:
        """Every violation in the file, before the baseline."""
        path = SourcePath(self._filename)
        for rule_type in self.rule_types:
            rule = rule_type()
            if rule.applies_to(path):
                yield from rule.check(self._tree)
