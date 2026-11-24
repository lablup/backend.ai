from collections.abc import Callable

import pytest

type Lint = Callable[[str, str], list[tuple[int, str]]]

ROW_FILE = "src/ai/backend/manager/models/session/row.py"


class TestRowMethodRule:
    @pytest.mark.parametrize(
        "method",
        [
            "def main_kernel(self): ...",
            "async def get(cls, session): ...",
            "@property\ndef main_kernel(self): ...",
            "@classmethod\nasync def get(cls, session): ...",
            "@staticmethod\ndef build(): ...",
            "@hybrid_property\ndef is_private(self): ...",
            "@validates('name')\ndef validate_name(self, key, value): ...",
            "def _private_helper(self): ...",
        ],
    )
    def test_method_other_than_conversion_fails(self, lint: Lint, method: str) -> None:
        body = "\n".join(f"    {line}" for line in method.splitlines())
        source = f"class SessionRow(Base):\n    id = Column()\n\n{body}\n"
        violations = lint(ROW_FILE, source)
        assert [code for _, code in violations] == ["BAI302"]

    def test_class_subclassing_base_is_checked(self, lint: Lint) -> None:
        source = """
            class Session(Base):
                def get(self): ...
        """
        assert lint(ROW_FILE, source) == [(3, "BAI302")]

    def test_conversion_and_dunder_methods_pass(self, lint: Lint) -> None:
        source = """
            class SessionRow(Base):
                def __init__(self, id): ...

                def __str__(self): ...

                def to_data(self): ...

                @classmethod
                def from_data(cls, data): ...
        """
        assert lint(ROW_FILE, source) == []

    def test_class_other_than_row_passes(self, lint: Lint) -> None:
        source = """
            class SessionScope:
                def to_condition(self): ...

                def owner(self): ...
        """
        assert lint(ROW_FILE, source) == []

    def test_row_outside_models_passes(self, lint: Lint) -> None:
        source = """
            class SessionRow(Base):
                def get(self): ...
        """
        assert lint("src/ai/backend/manager/repositories/session/types.py", source) == []

    def test_migration_passes(self, lint: Lint) -> None:
        source = """
            class SessionRow(Base):
                def get(self): ...
        """
        filename = "src/ai/backend/manager/models/alembic/versions/abc_add.py"
        assert lint(filename, source) == []
