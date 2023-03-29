from typing import Any

import aiosqlite


class FilebrowserTrackerDB:
    def __init__(self, db_path: str):
        self.db_path = db_path

    async def __ainit__(self):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS containers (
                    container_id TEXT PRIMARY KEY,
                    container_name TEXT,
                    service_ip TEXT,
                    service_port INTEGER,
                    config TEXT,
                    status TEXT,
                    timestamp TEXT
                )
                """
            )
            await db.commit()

    @classmethod
    async def create(cls, db_path: str) -> "FilebrowserTrackerDB":
        self = cls(db_path)
        await self.__ainit__()
        return self

    async def get_all_containers(self) -> Any:
        async with aiosqlite.connect(self.db_path) as db:
            async with db.cursor() as cursor:
                await cursor.execute("SELECT * FROM containers;")
                rows = await cursor.fetchall()
        return rows

    async def get_filebrowser_by_container_id(self, container_id: str) -> Any:
        async with aiosqlite.connect(self.db_path) as db:
            async with db.cursor() as cursor:
                await cursor.execute(
                    "SELECT * FROM containers WHERE container_id=?", (container_id,)
                )
                row = await cursor.fetchone()
        return row

    async def insert_new_container(
        self,
        container_id: str,
        container_name: str,
        service_ip: str,
        service_port: int,
        config: dict[str, Any],
        status: str,
        timestamp: str,
    ):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT INTO containers (container_id, container_name, service_ip, service_port, config, status, timestamp) VALUES (?, ?, ?, ?, ?, ?, ?);",
                (
                    container_id,
                    container_name,
                    service_ip,
                    service_port,
                    str(config),
                    status,
                    timestamp,
                ),
            )
            await db.commit()

    async def delete_container_record(self, container_id: str) -> None:
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("DELETE FROM containers WHERE container_id=?", (container_id,))
            await db.commit()
