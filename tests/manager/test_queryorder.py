import pytest
import sqlalchemy as sa
from sqlalchemy.ext.declarative import declarative_base

from ai.backend.manager.models.minilang.ordering import QueryOrderParser


@pytest.fixture
def virtual_grid_db():
    engine = sa.engine.create_engine("sqlite:///:memory:", echo=False)
    base = declarative_base()
    metadata = base.metadata
    grid = sa.Table(
        "users",
        metadata,
        sa.Column("id", sa.Integer, sa.Sequence("user_id_seq"), primary_key=True),
        sa.Column("data1", sa.Integer),
        sa.Column("data2", sa.Float),
        sa.Column("data3", sa.String(10)),
    )
    metadata.create_all(engine)
    with engine.connect() as conn:
        conn.execute(
            grid.insert(),
            [
                {"data1": 10, "data2": 0.2, "data3": "a"},
                {"data1": 10, "data2": 0.1, "data3": "c"},
                {"data1": 20, "data2": 0.0, "data3": "b"},
                {"data1": 20, "data2": -0.1, "data3": "d"},
            ],
        )
        yield conn, grid
    engine.dispose()


def test_select_queries(virtual_grid_db) -> None:
    conn, grid = virtual_grid_db
    parser = QueryOrderParser()

    sa_query = parser.append_ordering(
        sa.select([grid.c.id]).select_from(grid),
        "+data1",
    )
    actual_ret = list(conn.execute(sa_query))
    test_ret = [(1,), (2,), (3,), (4,)]
    assert test_ret == actual_ret

    sa_query = parser.append_ordering(
        sa.select([grid.c.id]).select_from(grid),
        "-data1",
    )
    actual_ret = list(conn.execute(sa_query))
    test_ret = [(3,), (4,), (1,), (2,)]
    assert test_ret == actual_ret

    sa_query = parser.append_ordering(
        sa.select([grid.c.id]).select_from(grid),
        "-data1,+data2",
    )
    actual_ret = list(conn.execute(sa_query))
    test_ret = [(4,), (3,), (2,), (1,)]
    assert test_ret == actual_ret

    sa_query = parser.append_ordering(
        sa.select([grid.c.id]).select_from(grid),
        "-data1,+data3,-data2",
    )
    actual_ret = list(conn.execute(sa_query))
    test_ret = [(3,), (4,), (1,), (2,)]
    assert test_ret == actual_ret

    # default ordering
    sa_query = parser.append_ordering(
        sa.select([grid.c.id]).select_from(grid),
        "",
    )
    actual_ret = list(conn.execute(sa_query))
    test_ret = [(1,), (2,), (3,), (4,)]
    assert test_ret == actual_ret

    # without order marks, it's assumed to be ascending
    sa_query = parser.append_ordering(
        sa.select([grid.c.id]).select_from(grid),
        "data3,-data2,data1",
    )
    actual_ret = list(conn.execute(sa_query))
    test_ret = [(1,), (3,), (2,), (4,)]
    assert test_ret == actual_ret

    # invalid syntax
    with pytest.raises(ValueError):
        parser.append_ordering(
            sa.select([grid.c.id]).select_from(grid),
            "xxx",
        )


def test_column_map(virtual_grid_db) -> None:
    conn, grid = virtual_grid_db
    parser = QueryOrderParser(
        {
            "v1": "data1",
            "v2": "data2",
            "v3": "data3",
        }
    )

    sa_query = parser.append_ordering(
        sa.select([grid.c.id]).select_from(grid),
        "-v3",
    )
    actual_ret = list(conn.execute(sa_query))
    test_ret = [(4,), (2,), (3,), (1,)]
    assert test_ret == actual_ret

    # non-existent column in the column map
    with pytest.raises(ValueError):
        parser.append_ordering(
            sa.select([grid.c.id]).select_from(grid),
            "-data1,+data2",
        )
