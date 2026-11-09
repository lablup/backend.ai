from __future__ import annotations

from typing import Final

import sqlalchemy as sa
from sqlalchemy.engine import Connection

from ai.backend.manager.models.alembic.table_rebuild import TableRebuild

# Agent heartbeats. 26.9 stops recording them; agent start and stop are in the event log.
_HEARTBEAT: Final[str] = "entity_type = 'agent' AND operation = 'update' AND triggered_by IS NULL"


class AuditLogRebuild:
    """Rebuilds `audit_logs` into a new table without heartbeat rows.

    Fills `acted_as` and `action_name` while copying when the table lacks them.
    """

    _conn: Connection
    _rebuild: TableRebuild

    def __init__(self, conn: Connection) -> None:
        self._conn = conn
        self._rebuild = TableRebuild(conn, "audit_logs")

    def columns(self) -> dict[str, str]:
        return self._rebuild.columns()

    def run(self) -> None:
        columns = self._rebuild.columns()
        values = {name: self._rebuild.quote(name) for name in columns}
        self._rebuild.create_new_table()
        new_table = self._rebuild.new_table
        match columns.get("acted_as"):
            case None:
                self._execute(f"ALTER TABLE {new_table} ADD COLUMN acted_as UUID")
                values["acted_as"] = "triggered_by::uuid"
            case "uuid":
                pass
            case _:
                self._execute(
                    f"ALTER TABLE {new_table} ALTER COLUMN acted_as TYPE UUID USING acted_as::uuid"
                )
                values["acted_as"] = "acted_as::uuid"
        if "action_name" not in columns:
            self._execute(f"ALTER TABLE {new_table} ADD COLUMN action_name VARCHAR NOT NULL")
            values["action_name"] = "entity_type || ':' || operation"
        self._execute(
            f"INSERT INTO {new_table} ({', '.join(self._rebuild.quote(name) for name in values)})"
            f" SELECT {', '.join(values.values())} FROM audit_logs WHERE NOT ({_HEARTBEAT})"
        )
        if "action_name" not in columns:
            self._execute(f"CREATE INDEX ix_audit_logs_action_name ON {new_table} (action_name)")
        self._rebuild.replace()

    def _execute(self, statement: str) -> None:
        self._conn.execute(sa.text(statement))
