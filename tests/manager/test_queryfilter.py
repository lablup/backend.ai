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
    pgsql_addr = postgres_container[1]
    host = pgsql_addr.host
    port = pgsql_addr.port

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


@pytest.mark.asyncio
async def test_exclude_fields(virtual_user_db) -> None:
    """Test that exclude_fields parameter properly excludes fields from SQL generation."""
    conn, users = virtual_user_db
    parser = QueryFilterParser({
        "name": ("name", None),
        "age": ("age", None),
        "excluded_field": ("excluded_field", None),
    })

    # Test parsing with excluded field - should not raise error and should filter by other fields
    sa_query = parser.append_filter(
        sa.select([users.c.name, users.c.age]).select_from(users),
        '(name == "tester") & (age == 30) & (excluded_field == "ignored")',
        exclude_fields={"excluded_field"},
    )
    actual_ret = list(await conn.execute(sa_query))
    # Should only match by name and age, ignoring the excluded_field condition
    test_ret = [("tester", 30)]
    assert test_ret == actual_ret

    # Test with multiple excluded fields
    parser2 = QueryFilterParser({
        "name": ("name", None),
        "age": ("age", None),
        "field1": ("field1", None),
        "field2": ("field2", None),
    })

    sa_query = parser2.append_filter(
        sa.select([users.c.name, users.c.age]).select_from(users),
        '(name == "tester") & (field1 == "x") & (field2 == "y")',
        exclude_fields={"field1", "field2"},
    )
    actual_ret = list(await conn.execute(sa_query))
    # Should only match by name, ignoring both excluded fields
    test_ret = [("tester", 30)]
    assert test_ret == actual_ret

    # Test with parse_filter method
    where_clause = parser.parse_filter(
        users,
        '(name == "tester") & (excluded_field == "ignored")',
        exclude_fields={"excluded_field"},
    )
    sa_query = sa.select([users.c.name, users.c.age]).select_from(users).where(where_clause)
    actual_ret = list(await conn.execute(sa_query))
    test_ret = [("tester", 30)]
    assert test_ret == actual_ret

    # Test OR operation with excluded fields - this tests the fix for the TODO issue
    # where (excluded_field == "x") | (name == "tester") should NOT become always true
    sa_query = parser.append_filter(
        sa.select([users.c.name, users.c.age]).select_from(users),
        '(excluded_field == "x") | (name == "tester")',
        exclude_fields={"excluded_field"},
    )
    actual_ret = list(await conn.execute(sa_query))
    # Should only match by name, NOT return all rows
    test_ret = [("tester", 30)]
    assert test_ret == actual_ret

    # Test OR with both sides excluded - should return no rows (sa.false())
    sa_query = parser2.append_filter(
        sa.select([users.c.name, users.c.age]).select_from(users),
        '(field1 == "x") | (field2 == "y")',
        exclude_fields={"field1", "field2"},
    )
    actual_ret = list(await conn.execute(sa_query))
    test_ret = []  # Should return no rows
    assert test_ret == actual_ret

    # Test AND with both sides excluded - should return all rows (sa.true())
    sa_query = parser2.append_filter(
        sa.select([users.c.name, users.c.age]).select_from(users),
        '(field1 == "x") & (field2 == "y")',
        exclude_fields={"field1", "field2"},
    )
    actual_ret = list(await conn.execute(sa_query))
    # Should return all rows since both conditions are excluded (neutral for AND)
    assert len(actual_ret) == 4


def test_has_field() -> None:
    """Test the has_field method to avoid false positives from naive substring matching."""
    parser = QueryFilterParser({
        "project_name": ("project_name", None),
        "name": ("name", None),
    })

    # Test: field exists in filter expression
    assert parser.has_field('project_name == "test"', "project_name") is True

    # Test: field in complex expression
    assert (
        parser.has_field('(project_name ilike "test") & (name != "user")', "project_name") is True
    )
    assert (
        parser.has_field('(project_name ilike "test") | (name != "user")', "project_name") is True
    )

    # Test: field does NOT exist (false positive case from naive substring matching)
    # "project_name" appears in string literal but not as an actual field
    assert parser.has_field('name == "my_project_name_tag"', "project_name") is False

    # Test: field does not exist at all
    assert parser.has_field('name == "test"', "project_name") is False

    # Test: multiple occurrences of the field
    assert parser.has_field('project_name == "a" | project_name == "b"', "project_name") is True

    # Test: invalid filter expression - should return False
    assert parser.has_field("invalid!!!syntax", "project_name") is False
    assert parser.has_field("", "project_name") is False

    # Test: deeply nested expression - should not cause RecursionError
    # Build a deeply nested expression: ((((name == "x") & (name == "y")) & ...) & ...)
    deep_expr = 'name == "x"'
    for i in range(100):  # Create 100 levels of nesting
        deep_expr = f'({deep_expr} & name == "y{i}")'
    # Should work without RecursionError
    assert parser.has_field(deep_expr, "name") is True
    assert parser.has_field(deep_expr, "project_name") is False
