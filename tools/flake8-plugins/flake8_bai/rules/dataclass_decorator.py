import ast


class DataclassDecorator:
    """The `@dataclass` or `@dataclasses.dataclass` decorator of a class, if any."""

    _decorator: ast.expr | None

    def __init__(self, cls: ast.ClassDef) -> None:
        self._decorator = next(
            (d for d in cls.decorator_list if self._is_dataclass(d)),
            None,
        )

    @property
    def present(self) -> bool:
        return self._decorator is not None

    @property
    def frozen(self) -> bool:
        if not isinstance(self._decorator, ast.Call):
            return False
        return any(
            kw.arg == "frozen" and isinstance(kw.value, ast.Constant) and kw.value.value is True
            for kw in self._decorator.keywords
        )

    def _is_dataclass(self, decorator: ast.expr) -> bool:
        target = decorator.func if isinstance(decorator, ast.Call) else decorator
        match target:
            case ast.Name(id="dataclass"):
                return True
            case ast.Attribute(value=ast.Name(id="dataclasses"), attr="dataclass"):
                return True
        return False
