import unittest
import uuid
from datetime import datetime

import sqlalchemy
from dateutil.tz import tzutc

from ai.backend.manager.config import load as load_config
from ai.backend.manager.models import groups, kernels, users
from ai.backend.manager.models.utils import connect_database, sql_json_merge


async def create_kernel_row(
    conn: sqlalchemy.ext.asyncio.engine.AsyncConnection,
    group_id: uuid.UUID,
    user_uuid: uuid.UUID,
) -> str:
    session_id = str(uuid.uuid4()).replace('-', '')
    query = kernels.insert().values({
        'session_id': session_id,
        'domain_name': 'default',
        'group_id': group_id,
        'user_uuid': user_uuid,
        'occupied_slots': {},
        'repl_in_port': 0,
        'repl_out_port': 0,
        'stdin_port': 0,
        'stdout_port': 0,
    })
    await conn.execute(query)
    return session_id


async def select_kernel_row(
    conn: sqlalchemy.ext.asyncio.engine.AsyncConnection,
    session_id: uuid.UUID,
):
    query = kernels.select().select_from(kernels).where(kernels.c.session_id == session_id)
    result = await conn.execute(query)
    return result


async def delete_kernel_rows(
    conn: sqlalchemy.ext.asyncio.engine.AsyncConnection,
):
    query = kernels.delete()
    await conn.execute(query)

events = []


class SqlJsonMergeTestCase(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        events.append("setUp")

    async def asyncSetUp(self):
        events.append("asyncSetUp")
        self.config = load_config()
        async with connect_database(self.config) as db:
            async with db.begin() as conn:
                query = sqlalchemy.select([users.c.uuid]).select_from(users)
                result = await conn.execute(query)
                self.user_uuid, *_ = result.first()

                query = sqlalchemy.select([groups.c.id]).select_from(groups)
                result = await conn.execute(query)
                self.group_id, *_ = result.first()

                await conn.close()

    async def test_sql_json_merge_01(self):
        timestamp = datetime.now(tzutc()).isoformat()
        expected = {
            "kernel": {
                "PENDING": timestamp,
                "PREPARING": timestamp,
            },
        }
        async with connect_database(self.config) as db:
            async with db.begin() as conn:
                session_id = await create_kernel_row(conn, self.group_id, self.user_uuid)
                query = kernels.update().values({
                    'status_history': sql_json_merge(
                        kernels.c.status_history,
                        ('kernel',),
                        {
                            'PENDING': timestamp,
                            'PREPARING': timestamp,
                        },
                    ),
                }).where(kernels.c.session_id == session_id)
                await conn.execute(query)
                kernel, *_ = await select_kernel_row(conn, session_id)
        self.assertIsNotNone(kernel)
        self.assertEqual(kernel.status_history, expected)
        self.addAsyncCleanup(self.on_cleanup)

    async def test_sql_json_merge_02(self):
        timestamp = datetime.now(tzutc()).isoformat()
        expected = {
            "kernel": {
                "session": {
                    "PENDING": timestamp,
                    "PREPARING": timestamp,
                },
            },
        }
        async with connect_database(self.config) as db:
            async with db.begin() as conn:
                session_id = await create_kernel_row(conn, self.group_id, self.user_uuid)
                query = kernels.update().values({
                    'status_history': sql_json_merge(
                        kernels.c.status_history,
                        ('kernel', 'session',),
                        {
                            'PENDING': timestamp,
                            'PREPARING': timestamp,
                        },
                    ),
                }).where(kernels.c.session_id == session_id)
                await conn.execute(query)
                kernel, *_ = await select_kernel_row(conn, session_id)
        self.assertIsNotNone(kernel)
        self.assertEqual(kernel.status_history, expected)
        self.addAsyncCleanup(self.on_cleanup)

    async def test_sql_json_merge_03(self):
        timestamp = datetime.now(tzutc()).isoformat()
        expected = {
            "PENDING": [
                {},
                timestamp
            ],
        }
        async with connect_database(self.config) as db:
            async with db.begin() as conn:
                session_id = await create_kernel_row(conn, self.group_id, self.user_uuid)
                query = kernels.update().values({
                    'status_history': sql_json_merge(
                        kernels.c.status_history,
                        ('PENDING',),
                        timestamp,
                    ),
                }).where(kernels.c.session_id == session_id)
                await conn.execute(query)
                kernel, *_ = await select_kernel_row(conn, session_id)
        self.assertIsNotNone(kernel)
        self.assertEqual(kernel.status_history, expected)
        self.addAsyncCleanup(self.on_cleanup)

    async def test_sql_json_merge_04(self):
        timestamp = datetime.now(tzutc()).isoformat()
        expected = {
            "PENDING": timestamp,
            "PREPARING": timestamp,
        }
        async with connect_database(self.config) as db:
            async with db.begin() as conn:
                session_id = await create_kernel_row(conn, self.group_id, self.user_uuid)
                query = kernels.update().values({
                    'status_history': sql_json_merge(
                        kernels.c.status_history,
                        (),
                        {
                            'PENDING': timestamp,
                            'PREPARING': timestamp,
                        },
                    ),
                }).where(kernels.c.session_id == session_id)
                await conn.execute(query)
                kernel, *_ = await select_kernel_row(conn, session_id)
        self.assertIsNotNone(kernel)
        self.assertEqual(kernel.status_history, expected)
        self.addAsyncCleanup(self.on_cleanup)

    def tearDown(self):
        events.append("tearDown")

    async def asyncTearDown(self):
        events.append("asyncTearDown")
        async with connect_database(self.config) as db:
            async with db.begin() as conn:
                await delete_kernel_rows(conn)

    async def on_cleanup(self):
        events.append("cleanup")


if __name__ == "__main__":
    unittest.main()
