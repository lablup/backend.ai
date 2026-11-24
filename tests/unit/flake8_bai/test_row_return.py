from collections.abc import Callable

import pytest

type Lint = Callable[[str, str], list[tuple[int, str]]]

REPOSITORY_FILE = "src/ai/backend/manager/repositories/session/repository.py"


class TestRowReturnRule:
    @pytest.mark.parametrize(
        "annotation",
        [
            "SessionRow",
            "SessionRow | None",
            "list[SessionRow]",
            "Sequence[SessionRow]",
            "dict[str, SessionRow]",
            "tuple[SessionRow, int]",
            "models.SessionRow",
            '"SessionRow"',
        ],
    )
    def test_public_method_returning_row_fails(self, lint: Lint, annotation: str) -> None:
        source = f"""
            class SessionRepository:
                async def get_session(self) -> {annotation}:
                    ...
        """
        assert lint(REPOSITORY_FILE, source) == [(3, "BAI301")]

    def test_repositories_file_is_checked(self, lint: Lint) -> None:
        source = """
            class SessionRepositories:
                def first(self) -> SessionRow:
                    ...
        """
        filename = "src/ai/backend/manager/repositories/session/repositories.py"
        assert lint(filename, source) == [(3, "BAI301")]

    def test_public_method_returning_data_passes(self, lint: Lint) -> None:
        source = """
            class SessionRepository:
                async def get_session(self) -> SessionData | None:
                    ...
        """
        assert lint(REPOSITORY_FILE, source) == []

    def test_sqlalchemy_row_passes(self, lint: Lint) -> None:
        source = """
            class SessionRepository:
                async def get_session(self) -> Row[Any]:
                    ...
        """
        assert lint(REPOSITORY_FILE, source) == []

    def test_private_method_returning_row_passes(self, lint: Lint) -> None:
        source = """
            class SessionRepository:
                async def _get_session(self) -> SessionRow:
                    ...
        """
        assert lint(REPOSITORY_FILE, source) == []

    def test_db_source_returning_row_passes(self, lint: Lint) -> None:
        source = """
            class SessionDBSource:
                async def get_session(self) -> SessionRow:
                    ...
        """
        filename = "src/ai/backend/manager/repositories/session/db_source/db_source.py"
        assert lint(filename, source) == []
