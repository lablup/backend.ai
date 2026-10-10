from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.engine import Connection

from ai.backend.manager.models.alembic.table_rebuild import TableRebuild


class KernelUsageRecordRebuild:
    """Copies `kernel_usage_records` into a new table that carries `resource_group_id`.

    Rows whose resource group name does not resolve are not copied.
    """

    _conn: Connection
    _rebuild: TableRebuild

    def __init__(self, conn: Connection) -> None:
        self._conn = conn
        self._rebuild = TableRebuild(conn, "kernel_usage_records")

    def columns(self) -> dict[str, str]:
        return self._rebuild.columns()

    def run(self) -> None:
        names = [self._rebuild.quote(name) for name in self._rebuild.columns()]
        self._rebuild.create_new_table()
        new_table = self._rebuild.new_table
        self._conn.execute(
            sa.text(f"ALTER TABLE {new_table} ADD COLUMN resource_group_id UUID NOT NULL")
        )
        self._conn.execute(
            sa.text(
                f"INSERT INTO {new_table} ({', '.join(names)}, resource_group_id)"
                f" SELECT {', '.join(f'k.{name}' for name in names)}, sg.id"
                " FROM kernel_usage_records k JOIN scaling_groups sg ON k.resource_group = sg.name"
            )
        )
        self._rebuild.replace()
