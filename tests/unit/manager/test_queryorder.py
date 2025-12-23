import pytest
import sqlalchemy as sa
from sqlalchemy.ext.declarative import declarative_base

from ai.backend.manager.models.minilang.ordering import QueryOrderParser
from ai.backend.manager.models.utils import agg_to_array


@pytest.fixture
async def virtual_grid_db(database_engine):
    base = declarative_base()
    metadata = base.metadata
    grid = sa.Table(
        "test_query_order_users",
        metadata,
        sa.Column("id", sa.Integer, sa.Sequence("user_id_seq"), primary_key=True),
        sa.Column("data1", sa.Integer),
        sa.Column("data2", sa.Float),
        sa.Column("data3", sa.String(10)),
    )
    foreign_grid = sa.Table(
        "test_query_order_dogs",
        metadata,
        sa.Column("id", sa.Integer, sa.Sequence("dog_id_seq"), primary_key=True),
        sa.Column("user_id", sa.ForeignKey("test_query_order_users.id")),
        sa.Column("name", sa.String(10)),
    )

    def _create_tables(conn, *args, **kwargs):
        return metadata.create_all(conn, [grid, foreign_grid])

    def _drop_tables(conn, *args, **kwargs):
        return metadata.drop_all(conn, [grid, foreign_grid])

    async with database_engine.begin() as conn:
        await conn.run_sync(_create_tables)
        await conn.execute(
            grid.insert(),
            [
                {"data1": 10, "data2": 0.2, "data3": "a"},
                {"data1": 10, "data2": 0.1, "data3": "c"},
                {"data1": 20, "data2": 0.0, "data3": "b"},
                {"data1": 20, "data2": -0.1, "data3": "d"},
            ],
        )
        await conn.execute(
            foreign_grid.insert(),
            [
                {"user_id": 1, "name": "b"},
                {"user_id": 1, "name": "c"},
                {"user_id": 2, "name": "a"},
            ],
        )

        try:
            yield conn, grid, foreign_grid
        finally:
            await conn.run_sync(_drop_tables)


async def test_select_queries(virtual_grid_db) -> None:
    conn, grid, _ = virtual_grid_db
    parser = QueryOrderParser()

    sa_query = parser.append_ordering(
        sa.select([grid.c.id]).select_from(grid),
        "+data1",
    )
    actual_ret = list(await conn.execute(sa_query))
    test_ret = [(1,), (2,), (3,), (4,)]
    assert test_ret == actual_ret

    sa_query = parser.append_ordering(
        sa.select([grid.c.id]).select_from(grid),
        "-data1",
    )
    actual_ret = list(await conn.execute(sa_query))
    test_ret = [(3,), (4,), (1,), (2,)]
    assert test_ret == actual_ret

    sa_query = parser.append_ordering(
        sa.select([grid.c.id]).select_from(grid),
        "-data1,+data2",
    )
    actual_ret = list(await conn.execute(sa_query))
    test_ret = [(4,), (3,), (2,), (1,)]
    assert test_ret == actual_ret

    sa_query = parser.append_ordering(
        sa.select([grid.c.id]).select_from(grid),
        "-data1,+data3,-data2",
    )
    actual_ret = list(await conn.execute(sa_query))
    test_ret = [(3,), (4,), (1,), (2,)]
    assert test_ret == actual_ret

    # default ordering
    sa_query = parser.append_ordering(
        sa.select([grid.c.id]).select_from(grid),
        "",
    )
    actual_ret = list(await conn.execute(sa_query))
    test_ret = [(1,), (2,), (3,), (4,)]
    assert test_ret == actual_ret

    # without order marks, it's assumed to be ascending
    sa_query = parser.append_ordering(
        sa.select([grid.c.id]).select_from(grid),
        "data3,-data2,data1",
    )
    actual_ret = list(await conn.execute(sa_query))
    test_ret = [(1,), (3,), (2,), (4,)]
    assert test_ret == actual_ret

    # invalid syntax
    with pytest.raises(ValueError):
        parser.append_ordering(
            sa.select([grid.c.id]).select_from(grid),
            "xxx",
        )


async def test_column_map(virtual_grid_db) -> None:
    conn, grid, _ = virtual_grid_db
    parser = QueryOrderParser({
        "v1": ("data1", None),
        "v2": ("data2", None),
        "v3": ("data3", None),
    })

    sa_query = parser.append_ordering(
        sa.select([grid.c.id]).select_from(grid),
        "-v3",
    )
    actual_ret = list(await conn.execute(sa_query))
    test_ret = [(4,), (2,), (3,), (1,)]
    assert test_ret == actual_ret

    # non-existent column in the column map
    with pytest.raises(ValueError):
        parser.append_ordering(
            sa.select([grid.c.id]).select_from(grid),
            "-data1,+data2",
        )


async def test_aggregated_foreign_fields(virtual_grid_db) -> None:
    conn, grid, foreign_grid = virtual_grid_db
    parser = QueryOrderParser({
        "dogs_name": ("test_query_order_dogs_name", agg_to_array),
    })

    orig_query = (
        sa.select([
            grid.c.id,
            agg_to_array(foreign_grid.c.name).label("dogs_name"),
        ])
        .select_from(sa.join(grid, foreign_grid, grid.c.id == foreign_grid.c.user_id))
        .group_by(grid)
    )
    sa_query = parser.append_ordering(
        orig_query,
        "dogs_name",
    )
    actual_ret = list(await conn.execute(sa_query))
    test_ret = [(2, ["a"]), (1, ["b", "c"])]
    assert test_ret == actual_ret
