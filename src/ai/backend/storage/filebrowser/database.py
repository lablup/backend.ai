from typing import Any

import sqlalchemy as sa


class FilebrowserTrackerDB:
    def __init__(self, db_path: str):
        self.meta = sa.MetaData()
        self.containers = sa.Table(
            "containers",
            self.meta,
            sa.Column("container_id", sa.String, primary_key=True),
            sa.Column("container_name", sa.String),
            sa.Column("service_ip", sa.String),
            sa.Column("service_port", sa.Integer),
            sa.Column("config", sa.Text),
            sa.Column("status", sa.String),
            sa.Column("timestamp", sa.String),
        )
        self.db_path = db_path
        self.url = f"sqlite:///{str(db_path)}"
        self._engine = sa.engine
        self.engine = sa.create_engine(self.url)

        insp = sa.inspect(self.engine)
        if "containers" not in insp.get_table_names():
            self.meta.create_all(self.engine)

    async def get_all_containers(self) -> Any:
        with self.engine.connect() as connection:
            rows = connection.execute(self.containers.select())
        return rows

    async def get_filebrowser_by_container_id(self, container_id: str) -> Any:
        with self.engine.connect() as connection:
            rows = connection.execute(
                self.containers.select().where(
                    self.containers.c.container_id == container_id,
                ),
            )
        return rows

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
        with self.engine.connect() as connection:
            ins = self.containers.insert().values(
                container_id=container_id,
                container_name=container_name,
                service_ip=service_ip,
                service_port=int(service_port),
                config=str(config),
                status=status,
                timestamp=timestamp,
            )
            connection.execute(ins)

    async def delete_container_record(self, container_id: str) -> None:
        with self.engine.connect() as connection:
            del_sql = self.containers.delete().where(
                self.containers.c.container_id == container_id,
            )
            connection.execute(del_sql)
