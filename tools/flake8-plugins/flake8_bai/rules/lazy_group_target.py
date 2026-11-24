import ast
from collections.abc import Iterator
from pathlib import Path
from typing import override

from flake8_bai.codes import BAICode
from flake8_bai.rules.base import Rule, SourcePath, Violation


class ModuleNames:
    """The names a module binds at its top level, read from its source without importing it."""

    _names: set[str]
    _open: bool

    def __init__(self, tree: ast.Module) -> None:
        self._names = set()
        self._open = False
        self._collect(tree.body)

    def has(self, name: str) -> bool:
        return self._open or name in self._names

    def _collect(self, body: list[ast.stmt]) -> None:
        for node in body:
            match node:
                case ast.FunctionDef() | ast.AsyncFunctionDef() | ast.ClassDef():
                    self._names.add(node.name)
                    if node.name == "__getattr__":
                        self._open = True
                case ast.Import() | ast.ImportFrom():
                    for alias in node.names:
                        if alias.name == "*":
                            self._open = True
                        else:
                            self._names.add(alias.asname or alias.name.split(".")[0])
                case ast.Assign() | ast.AnnAssign() | ast.AugAssign():
                    targets = node.targets if isinstance(node, ast.Assign) else [node.target]
                    for target in targets:
                        self._names.update(
                            n.id for n in ast.walk(target) if isinstance(n, ast.Name)
                        )
                case ast.If() | ast.For() | ast.While() | ast.With() | ast.AsyncWith():
                    self._collect(node.body)
                    self._collect(getattr(node, "orelse", []))
                case ast.Try() | ast.TryStar():
                    self._collect(node.body)
                    for handler in node.handlers:
                        self._collect(handler.body)
                    self._collect(node.orelse)
                    self._collect(node.finalbody)


class LazyGroupTargetRule(Rule):
    """BAI401: the module file and top-level name a `LazyGroup` `import_name` points at exist.

    The module is looked up under the nearest ancestor directory of the checked file that holds its top package.
    """

    @override
    def applies_to(self, path: SourcePath) -> bool:
        return True

    @override
    def check(self, tree: ast.Module) -> Iterator[Violation]:
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call) or not self._is_lazy_group(node):
                continue
            for keyword in node.keywords:
                if keyword.arg != "import_name":
                    continue
                value = keyword.value
                if not isinstance(value, ast.Constant) or not isinstance(value.value, str):
                    continue
                if not self._exists(value.value):
                    yield Violation(value.lineno, value.col_offset, BAICode.LAZY_GROUP_TARGET)

    def _is_lazy_group(self, call: ast.Call) -> bool:
        if self._is_lazy_group_name(call.func):
            return True
        return any(k.arg == "cls" and self._is_lazy_group_name(k.value) for k in call.keywords)

    def _is_lazy_group_name(self, node: ast.expr) -> bool:
        match node:
            case ast.Name(id="LazyGroup") | ast.Attribute(attr="LazyGroup"):
                return True
        return False

    def _exists(self, import_name: str) -> bool:
        module, sep, name = import_name.partition(":")
        if not sep or not module or not name:
            return False
        module_file = self._module_file(module)
        if module_file is None:
            return False
        tree = ast.parse(module_file.read_text(encoding="utf-8"))
        return ModuleNames(tree).has(name)

    def _module_file(self, module: str) -> Path | None:
        parts = module.split(".")
        for root in Path(self._path.filename).resolve().parents:
            if not (root / parts[0]).is_dir():
                continue
            base = root.joinpath(*parts)
            for candidate in (base.with_suffix(".py"), base / "__init__.py"):
                if candidate.is_file():
                    return candidate
            return None
        return None
