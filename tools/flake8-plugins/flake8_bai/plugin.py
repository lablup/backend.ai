import ast
from collections.abc import Iterator

from flake8_bai.rules.action_frozen import ActionFrozenRule
from flake8_bai.rules.action_pair import ActionPairRule
from flake8_bai.rules.base import Rule, SourcePath
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

    _tree: ast.Module
    _path: SourcePath

    def __init__(self, tree: ast.Module, filename: str) -> None:
        self._tree = tree
        self._path = SourcePath(filename)

    def run(self) -> Iterator[tuple[int, int, str, type["Plugin"]]]:
        for rule_type in self.rule_types:
            rule = rule_type()
            if not rule.applies_to(self._path):
                continue
            for violation in rule.check(self._tree):
                message = f"{violation.code.code} {violation.code.message}"
                yield violation.line, violation.col, message, type(self)
