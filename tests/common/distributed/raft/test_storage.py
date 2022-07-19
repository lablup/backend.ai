import random

import pytest

from ai.backend.common.distributed.raft.protos import raft_pb2
from ai.backend.common.distributed.raft.storage import SqliteLogStorage


@pytest.mark.asyncio
async def test_sqlite_storage() -> None:
    storage = SqliteLogStorage(volatile=True)

    n = 16
    entries = tuple(
        raft_pb2.Log(index=i, term=pow(i, 2), command="+OK\r\n")
        for i in range(1, n + 1)
    )
    await storage.append_entries(entries)

    count = await storage.size()
    assert count == len(entries)

    random_index = random.randint(0, count - 1)
    row = await storage.get(random_index)
    assert row is not None
    assert row.index == random_index

    row = await storage.last()
    assert row is not None
    assert row.index == n

    random_index = random.randint(1, count - 1)
    await storage.splice(random_index)

    count = await storage.size()
    assert count == (random_index - 1)
