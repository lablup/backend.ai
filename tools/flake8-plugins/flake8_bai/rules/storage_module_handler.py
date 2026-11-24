import ast
from collections.abc import Iterator
from typing import override

from flake8_bai.codes import BAICode
from flake8_bai.rules.base import Rule, SourcePath, Violation


class StorageModuleHandlerRule(Rule):
    """BAI403: no module-level aiohttp handler under storage `api/`.

    A handler is an `async def` whose only parameter is annotated `web.Request` or `Request`.
    """

    @override
    def applies_to(self, path: SourcePath) -> bool:
        return path.is_under("src/ai/backend/storage/api")

    @override
    def check(self, tree: ast.Module) -> Iterator[Violation]:
        for node in tree.body:
            if isinstance(node, ast.AsyncFunctionDef) and self._is_handler(node.args):
                yield Violation(node.lineno, node.col_offset, BAICode.STORAGE_MODULE_HANDLER)

    def _is_handler(self, args: ast.arguments) -> bool:
        params = [*args.posonlyargs, *args.args, *args.kwonlyargs]
        if len(params) != 1 or args.vararg or args.kwarg:
            return False
        match params[0].annotation:
            case ast.Name(id="Request") | ast.Attribute(attr="Request"):
                return True
        return False
