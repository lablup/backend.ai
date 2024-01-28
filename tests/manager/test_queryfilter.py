import enum
import secrets

import pytest
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncEngine
from sqlalchemy.ext.declarative import declarative_base

from ai.backend.manager.models.minilang import ArrayFieldItem, JSONFieldItem
from ai.backend.manager.models.minilang.queryfilter import QueryFilterParser
from ai.backend.testutils.bootstrap import postgres_container  # noqa


class UserTypes(enum.Enum):
    ADMIN = 0
    USER = 1


@pytest.fixture
async def virtual_user_db(postgres_container):  # noqa
    host, port = postgres_container[1]
    db_id = secrets.token_hex(16)
    engine = sa.engine.create_engine(
        f"postgresql+asyncpg://postgres:develove@{host}:{port}/testing", echo=False
    )
    async_engine = AsyncEngine(engine)
    base = declarative_base()
    metadata = base.metadata
    users = sa.Table(
        f"test_users_{db_id}",
        metadata,
        sa.Column("id", sa.Integer, sa.Sequence("user_id_seq"), primary_key=True),
        sa.Column("name", sa.String(50)),
        sa.Column("full_name", sa.String(50)),
        sa.Column("type", sa.Enum(UserTypes)),
        sa.Column("age", sa.Integer),
        sa.Column("is_active", sa.Boolean),
        sa.Column("value", sa.Float, nullable=True),
        sa.Column("data", sa.JSON),
        sa.Column("tags", sa.ARRAY(sa.Text())),
    )

    def _create_all_sync(conn, engine):
        metadata.create_all(engine, checkfirst=False)

    def _drop_all_sync(conn, engine):
        metadata.drop_all(engine, checkfirst=False)

    async with async_engine.begin() as conn:
        await conn.run_sync(_create_all_sync, engine=engine)

    async with async_engine.begin() as conn:
        await conn.execute(
            users.insert(),
            [
                {
                    "name": "tester",
                    "full_name": "tester1",
                    "type": UserTypes.ADMIN,
                    "age": 30,
                    "is_active": True,
                    "value": 10.5,
                    "data": {"hobby": "piano"},
                    "tags": ["aaa", "bbb"],
                },
                {
                    "name": 'test"er',
                    "full_name": "tester2",
                    "type": UserTypes.USER,
                    "age": 40,
                    "is_active": True,
                    "value": None,
                    "data": {"hobby": "tennis"},
                    "tags": ["aaa", "ccc"],
                },
                {
                    "name": "test'er",
                    "full_name": "tester3",
                    "type": UserTypes.USER,
                    "age": 50,
                    "is_active": False,
                    "value": 2.33,
                    "data": {"hobby": "running"},
                    "tags": [],
                },
                {
                    "name": "tester ♪",
                    "full_name": "tester4",
                    "type": UserTypes.USER,
                    "age": 20,
                    "is_active": False,
                    "value": None,
                    "data": {"hobby": "cello"},
                    "tags": ["bbb", "ddd"],
                },
            ],
        )

        yield conn, users

    async with async_engine.begin() as conn:
        await conn.run_sync(_drop_all_sync, engine=engine)
    engine.dispose()


@pytest.mark.asyncio
async def test_select_queries(virtual_user_db) -> None:
    conn, users = virtual_user_db
    parser = QueryFilterParser()

    sa_query = parser.append_filter(
        sa.select([users.c.name, users.c.age]).select_from(users),
        'full_name == "tester1"',
    )
    actual_ret = list(await conn.execute(sa_query))
    test_ret = [("tester", 30)]
    assert test_ret == actual_ret

    sa_query = parser.append_filter(
        sa.select([users.c.name, users.c.age]).select_from(users),
        'name == "test\'er"',
    )
    actual_ret = list(await conn.execute(sa_query))
    test_ret = [("test'er", 50)]
    assert test_ret == actual_ret

    sa_query = parser.append_filter(
        sa.select([users.c.name, users.c.age]).select_from(users),
        'name == "test\\"er"',
    )
    actual_ret = list(await conn.execute(sa_query))
    test_ret = [('test"er', 40)]
    assert test_ret == actual_ret

    sa_query = parser.append_filter(
        sa.select([users.c.name, users.c.age]).select_from(users),
        '(full_name == "tester1")',
    )
    actual_ret = list(await conn.execute(sa_query))
    test_ret = [("tester", 30)]
    assert test_ret == actual_ret

    sa_query = parser.append_filter(
        sa.select([users.c.name, users.c.age]).select_from(users),
        'full_name in ["tester1", "tester3", "tester9"]',
    )
    actual_ret = list(await conn.execute(sa_query))
    test_ret = [("tester", 30), ("test'er", 50)]
    assert test_ret == actual_ret

    sa_query = parser.append_filter(
        sa.select([users.c.name, users.c.age]).select_from(users),
        'type in ["USER", "ADMIN"]',
    )
    actual_ret = list(await conn.execute(sa_query))
    assert len(actual_ret) == 4

    sa_query = parser.append_filter(
        sa.select([users.c.name, users.c.age]).select_from(users),
        'full_name == "tester1" & age == 20',
    )
    actual_ret = list(await conn.execute(sa_query))
    test_ret = []
    assert test_ret == actual_ret

    sa_query = parser.append_filter(
        sa.select([users.c.name, users.c.age]).select_from(users),
        '(full_name == "tester1") & (age == 20)',
    )
    actual_ret = list(await conn.execute(sa_query))
    test_ret = []
    assert test_ret == actual_ret

    sa_query = parser.append_filter(
        sa.select([users.c.name, users.c.age]).select_from(users),
        '(full_name == "tester1") | (age == 20)',
    )
    actual_ret = list(await conn.execute(sa_query))
    test_ret = [("tester", 30), ("tester ♪", 20)]
    assert test_ret == actual_ret

    sa_query = parser.append_filter(
        sa.select([users.c.name, users.c.age]).select_from(users),
        '(name contains "test") & (age > 30) & (is_active is true)',
    )
    actual_ret = list(await conn.execute(sa_query))
    test_ret = [('test"er', 40)]
    assert test_ret == actual_ret

    sa_query = parser.append_filter(
        sa.select([users.c.name, users.c.age]).select_from(users),
        "value isnot null",
    )
    actual_ret = list(await conn.execute(sa_query))
    test_ret = [("tester", 30), ("test'er", 50)]
    assert test_ret == actual_ret

    sa_query = parser.append_filter(
        sa.select([users.c.name, users.c.age]).select_from(users),
        "value is null",
    )
    actual_ret = list(await conn.execute(sa_query))
    test_ret = [('test"er', 40), ("tester ♪", 20)]
    assert test_ret == actual_ret

    sa_query = parser.append_filter(
        sa.select([users.c.name, users.c.age]).select_from(users),
        "value is null | value isnot null",
    )
    actual_ret = list(await conn.execute(sa_query))
    assert len(actual_ret) == 4  # all rows

    sa_query = parser.append_filter(
        sa.select([users.c.name, users.c.age]).select_from(users),
        "value < 9.4",
    )
    actual_ret = list(await conn.execute(sa_query))
    test_ret = [("test'er", 50)]  # Note: null values are not matched
    assert test_ret == actual_ret

    # invalid syntax
    with pytest.raises(ValueError):
        parser.append_filter(
            sa.select([users.c.name, users.c.age]).select_from(users),
            "",
        )
    with pytest.raises(ValueError):
        parser.append_filter(
            sa.select([users.c.name, users.c.age]).select_from(users),
            "!!!",
        )
    with pytest.raises(ValueError):
        parser.append_filter(
            sa.select([users.c.name, users.c.age]).select_from(users),
            "123",
        )
    with pytest.raises(ValueError):
        parser.append_filter(
            sa.select([users.c.name, users.c.age]).select_from(users),
            '"abc"',
        )
    with pytest.raises(ValueError):
        parser.append_filter(
            sa.select([users.c.name, users.c.age]).select_from(users),
            "name =",
        )

    # invalid value type
    # => This case is handled during the actual execution of SQL statements
    #    in the database, not when preparing statements.
    #    So it is the out of scope issue.
    # with pytest.raises(ValueError):
    #     parser.append_filter(
    #         sa.select([users.c.name, users.c.age]).select_from(users),
    #         "full_name == 123",
    #     )

    # non-existent column
    with pytest.raises(ValueError):
        parser.append_filter(
            sa.select([users.c.name, users.c.age]).select_from(users),
            "xyz == 123",
        )


@pytest.mark.asyncio
async def test_modification_queries(virtual_user_db) -> None:
    conn, users = virtual_user_db
    parser = QueryFilterParser()

    sa_query = parser.append_filter(
        sa.update(users).values({"name": "hello"}),
        'full_name == "tester1"',
    )
    result = await conn.execute(sa_query)
    assert result.rowcount == 1

    sa_query = parser.append_filter(
        sa.delete(users),
        'full_name like "tester%"',
    )
    result = await conn.execute(sa_query)
    assert result.rowcount == 4


@pytest.mark.asyncio
async def test_fieldspec(virtual_user_db) -> None:
    conn, users = virtual_user_db
    parser = QueryFilterParser({
        "n1": ("name", None),
        "n2": ("full_name", lambda s: s.lower()),
        "t1": ("type", lambda s: UserTypes[s]),
        "hobby": (JSONFieldItem("data", "hobby"), None),
        "tag": (ArrayFieldItem("tags"), None),
    })

    sa_query = parser.append_filter(
        sa.select([users.c.name, users.c.age]).select_from(users),
        'n1 == "tester"',
    )
    actual_ret = list(await conn.execute(sa_query))
    test_ret = [("tester", 30)]
    assert test_ret == actual_ret

    sa_query = parser.append_filter(
        sa.select([users.c.name, users.c.age]).select_from(users),
        'n2 == "TESTER1"',
    )
    actual_ret = list(await conn.execute(sa_query))
    test_ret = [("tester", 30)]
    assert test_ret == actual_ret

    sa_query = parser.append_filter(
        sa.select([users.c.name, users.c.age]).select_from(users),
        'n2 in ["TESTER2", "TESTER4"]',
    )
    actual_ret = list(await conn.execute(sa_query))
    test_ret = [('test"er', 40), ("tester ♪", 20)]
    assert test_ret == actual_ret

    sa_query = parser.append_filter(
        sa.select([users.c.name, users.c.age]).select_from(users),
        't1 in ["USER", "ADMIN"]',
    )
    actual_ret = list(await conn.execute(sa_query))
    assert len(actual_ret) == 4

    # A fieldspec to match against a field in a JSON object column
    sa_query = parser.append_filter(
        sa.select([users.c.name, users.c.age]).select_from(users),
        'hobby == "piano"',
    )
    actual_ret = list(await conn.execute(sa_query))
    test_ret = [("tester", 30)]
    assert test_ret == actual_ret

    sa_query = parser.append_filter(
        sa.select([users.c.name, users.c.age]).select_from(users),
        'tag == "bbb"',
    )
    actual_ret = list(await conn.execute(sa_query))
    test_ret = [("tester", 30), ("tester ♪", 20)]
    assert test_ret == actual_ret

    sa_query = parser.append_filter(
        sa.select([users.c.name, users.c.age]).select_from(users),
        'tag like "%b%"',
    )
    actual_ret = list(await conn.execute(sa_query))
    test_ret = [("tester", 30), ("tester ♪", 20)]
    assert test_ret == actual_ret

    # non-existent column in fieldspec
    with pytest.raises(ValueError):
        parser.append_filter(
            sa.select([users.c.name, users.c.age]).select_from(users),
            'full_name == "TESTER1"',
        )

    # non-existent enum value
    with pytest.raises(ValueError):
        parser.append_filter(
            sa.select([users.c.name, users.c.age]).select_from(users),
            't1 == "XYZ"',
        )
