import ast
import enum


class ActionClassKind(enum.Enum):
    ACTION = "Action"
    RESULT = "ActionResult"


class ActionClass:
    """A module-level class in the Action or ActionResult family."""

    node: ast.ClassDef
    kind: ActionClassKind

    def __init__(self, node: ast.ClassDef, kind: ActionClassKind) -> None:
        self.node = node
        self.kind = kind


class ActionClassFinder:
    """Classifies a class by its bases first and by its own name where no base decides.

    Bases are followed through this file's classes; an imported base is classified by its name.
    """

    _framework_package = "ai.backend.manager.actions"

    _local_classes: dict[str, ast.ClassDef]
    _import_origins: dict[str, str]

    def __init__(self, tree: ast.Module) -> None:
        self._local_classes = {n.name: n for n in tree.body if isinstance(n, ast.ClassDef)}
        self._import_origins = {
            alias.asname or alias.name: node.module
            for node in tree.body
            if isinstance(node, ast.ImportFrom) and node.module and node.level == 0
            for alias in node.names
        }

    def find(self) -> list[ActionClass]:
        found: list[ActionClass] = []
        for node in self._local_classes.values():
            kind = self._classify(node, {node.name})
            if kind is not None:
                found.append(ActionClass(node, kind))
        return found

    def _classify(self, node: ast.ClassDef, visited: set[str]) -> ActionClassKind | None:
        for base in node.bases:
            name = self._base_name(base)
            if name is None or name in visited:
                continue
            kind = self._classify_base(name, visited | {name})
            if kind is not None:
                return kind
        return self._classify_name(node.name)

    def _classify_base(self, name: str, visited: set[str]) -> ActionClassKind | None:
        local = self._local_classes.get(name)
        if local is not None:
            return self._classify(local, visited)
        origin = self._import_origins.get(name, "")
        if origin == self._framework_package or origin.startswith(f"{self._framework_package}."):
            if name.endswith("Result"):
                return ActionClassKind.RESULT
            if name.endswith("Action"):
                return ActionClassKind.ACTION
            return None
        return self._classify_name(name)

    def _classify_name(self, name: str) -> ActionClassKind | None:
        if name.endswith(ActionClassKind.RESULT.value):
            return ActionClassKind.RESULT
        if name.endswith(ActionClassKind.ACTION.value):
            return ActionClassKind.ACTION
        return None

    def _base_name(self, base: ast.expr) -> str | None:
        target = base.value if isinstance(base, ast.Subscript) else base
        if isinstance(target, ast.Name):
            return target.id
        return None
