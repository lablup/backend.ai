import ast
from collections.abc import Iterator

from flake8_bai.codes import BAICode
from flake8_bai.rules.action_class import ActionClassFinder
from flake8_bai.rules.base import Rule, SourcePath, Violation
from flake8_bai.rules.dataclass_decorator import DataclassDecorator


class ActionFrozenRule(Rule):
    """BAI102: an Action or ActionResult dataclass under `manager/services` is frozen."""

    def applies_to(self, path: SourcePath) -> bool:
        return path.is_under("src/ai/backend/manager/services")

    def check(self, tree: ast.Module) -> Iterator[Violation]:
        for action_class in ActionClassFinder(tree).find():
            decorator = DataclassDecorator(action_class.node)
            if decorator.present and not decorator.frozen:
                node = action_class.node
                yield Violation(node.lineno, node.col_offset, BAICode.ACTION_NOT_FROZEN)
