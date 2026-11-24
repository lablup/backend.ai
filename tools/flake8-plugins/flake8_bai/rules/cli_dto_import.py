import ast
from collections.abc import Iterator
from typing import override

from flake8_bai.codes import BAICode
from flake8_bai.rules.base import Rule, SourcePath, Violation


class CliDtoImportRule(Rule):
    """BAI204: a module under `client/cli/v2` imports `ai.backend.common.dto` inside a function.

    An import under `if TYPE_CHECKING:` does not run and passes.
    """

    _package = "ai.backend.common.dto"

    @override
    def applies_to(self, path: SourcePath) -> bool:
        return path.is_under("src/ai/backend/client/cli/v2")

    @override
    def check(self, tree: ast.Module) -> Iterator[Violation]:
        for node in self._module_level(tree.body):
            if self._imports_dto(node):
                yield Violation(node.lineno, node.col_offset, BAICode.CLI_DTO_IMPORT)

    def _module_level(self, body: list[ast.stmt]) -> Iterator[ast.stmt]:
        """Statements that run on import: function bodies and `if TYPE_CHECKING:` are skipped."""
        for node in body:
            yield node
            match node:
                case ast.FunctionDef() | ast.AsyncFunctionDef():
                    pass
                case ast.If(test=test, orelse=orelse) if self._is_type_checking(test):
                    yield from self._module_level(orelse)
                case ast.Try(handlers=handlers) | ast.TryStar(handlers=handlers):
                    yield from self._module_level(node.body)
                    for handler in handlers:
                        yield from self._module_level(handler.body)
                    yield from self._module_level(node.orelse)
                    yield from self._module_level(node.finalbody)
                case ast.If() | ast.For() | ast.While() | ast.With() | ast.ClassDef():
                    yield from self._module_level(node.body)
                    yield from self._module_level(getattr(node, "orelse", []))

    def _is_type_checking(self, test: ast.expr) -> bool:
        match test:
            case ast.Name(id="TYPE_CHECKING") | ast.Attribute(attr="TYPE_CHECKING"):
                return True
        return False

    def _imports_dto(self, node: ast.stmt) -> bool:
        match node:
            case ast.Import(names=names):
                return any(self._is_dto(alias.name) for alias in names)
            case ast.ImportFrom(module=module, names=names, level=0) if module:
                if self._is_dto(module):
                    return True
                return any(self._is_dto(f"{module}.{alias.name}") for alias in names)
        return False

    def _is_dto(self, module: str) -> bool:
        return module == self._package or module.startswith(f"{self._package}.")
