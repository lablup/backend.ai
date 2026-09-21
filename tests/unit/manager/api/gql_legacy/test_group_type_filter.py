"""Project type filtering in the legacy group_nodes query filter."""

from __future__ import annotations

import pytest
import sqlalchemy as sa

from ai.backend.manager.api.gql_legacy.group import GroupNode
from ai.backend.manager.data.project.types import ProjectType
from ai.backend.manager.models.minilang.queryfilter import QueryFilterParser
from ai.backend.manager.models.project import groups


def _compiled_where(filter_expr: str) -> sa.sql.compiler.SQLCompiler:
    query = QueryFilterParser(GroupNode.queryfilter_fieldspec).append_filter(
        sa.select(groups.c.id), filter_expr
    )
    where_clause = query.whereclause
    assert where_clause is not None
    return where_clause.compile()


@pytest.mark.parametrize("given", ["PERSONAL", "personal"])
def test_type_filter_accepts_both_the_enum_key_and_its_value(given: str) -> None:
    compiled = _compiled_where(f'type == "{given}"')

    assert "groups.type" in str(compiled)
    assert ProjectType.PERSONAL in compiled.params.values()


def test_type_filter_supports_exclusion() -> None:
    compiled = _compiled_where('type != "PERSONAL"')

    assert "groups.type !=" in str(compiled)
    assert ProjectType.PERSONAL in compiled.params.values()


def test_type_filter_rejects_an_unknown_type() -> None:
    with pytest.raises(ValueError):
        _compiled_where('type == "nonexistent"')
