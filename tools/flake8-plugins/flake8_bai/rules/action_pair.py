import ast
from collections.abc import Iterator

from flake8_bai.codes import BAICode
from flake8_bai.rules.action_class import ActionClassFinder, ActionClassKind
from flake8_bai.rules.base import Rule, SourcePath, Violation


class ActionPairRule(Rule):
    """BAI103: a file under `manager/services` holds at most one Action and one ActionResult."""

    def applies_to(self, path: SourcePath) -> bool:
        return path.is_under("src/ai/backend/manager/services")

    def check(self, tree: ast.Module) -> Iterator[Violation]:
        seen: set[ActionClassKind] = set()
        for action_class in ActionClassFinder(tree).find():
            if action_class.kind in seen:
                node = action_class.node
                yield Violation(node.lineno, node.col_offset, BAICode.ACTION_PAIR)
            seen.add(action_class.kind)
