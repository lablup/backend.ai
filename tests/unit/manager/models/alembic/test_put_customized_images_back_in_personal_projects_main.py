"""The main-only copy of the personal-project backfill runs what the revision the 26.9
branch carries runs."""

from __future__ import annotations

import importlib.util
import pathlib
from types import ModuleType

import pytest

from ai.backend.manager.models.alembic.versions import (
    ae7f2b1fa98c_put_customized_images_back_in_personal_projects_main as copy,
)
from ai.backend.manager.models.alembic.versions import (
    d1117da8d8bd_put_customized_images_back_in_personal_projects as original,
)


class TestTheCopyRunsTheSameStatements:
    @pytest.mark.parametrize(
        "statement",
        ["_ADD_MEMBERSHIPS", "_ADD_BINDINGS", "_REMOVE_MEMBERSHIPS", "_REMOVE_BINDINGS"],
    )
    def test_each_statement_matches(self, statement: str) -> None:
        assert str(getattr(copy, statement)) == str(getattr(original, statement))

    def test_the_module_executes_outside_sys_modules(self) -> None:
        path = pathlib.Path(copy.__file__)
        spec = importlib.util.spec_from_file_location(path.stem, path)
        assert spec is not None and spec.loader is not None
        module: ModuleType = importlib.util.module_from_spec(spec)

        spec.loader.exec_module(module)

        assert module.revision == copy.revision
        assert module.down_revision == copy.down_revision
