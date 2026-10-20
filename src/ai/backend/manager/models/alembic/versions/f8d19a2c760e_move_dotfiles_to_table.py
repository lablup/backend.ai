"""Unpack keypair dotfiles into entity-owned file rows."""

from collections.abc import Iterator
from itertools import batched, groupby
from typing import Any

import msgpack
import sqlalchemy as sa
from alembic import op
from sqlalchemy.engine import Connection, RowMapping

revision = "f8d19a2c760e"  # Part of: NEXT_RELEASE_VERSION
down_revision = "c7e2a91f4d36"
branch_labels = None
depends_on = None


def _batched_rows(
    conn: Connection,
    query: sa.sql.Select[Any],
) -> Iterator[RowMapping]:
    """Read by owner and primary key without retaining a cursor across writes or DDL."""
    owner_column, id_column = query.selected_columns.owner, query.selected_columns.id
    last: tuple[Any, Any] | None = None
    while True:
        batch_query = query.order_by(owner_column, id_column).limit(1000)
        if last is not None:
            batch_query = batch_query.where(sa.tuple_(owner_column, id_column) > last)
        rows = conn.execute(batch_query).mappings().all()
        if not rows:
            return
        yield from rows
        last = (rows[-1]["owner"], rows[-1]["id"])


def _unpack_dotfiles(rows: Iterator[RowMapping]) -> Iterator[dict[str, Any]]:
    """Strip NUL, which text cannot hold."""
    for owner, owner_keys in groupby(rows, key=lambda row: row["owner"]):
        files: dict[tuple[str, str, str], bool] = {}
        for keypair in owner_keys:
            if not keypair["dotfiles"]:
                continue
            for entry in msgpack.unpackb(keypair["dotfiles"], raw=False):
                path, perm, data = (
                    entry[field].replace("\x00", "") for field in ("path", "perm", "data")
                )
                key = (path, perm, data)
                files[key] = files.get(key, False) or keypair["is_default"]
        default_paths: set[str] = set()
        for (path, perm, data), is_default in files.items():
            # Stripping NUL can merge two default paths; the later one becomes a variant.
            is_default = is_default and path not in default_paths
            if is_default:
                default_paths.add(path)
            yield {
                "entity_type": "user",
                "entity_id": owner,
                "path": path,
                "perm": perm,
                "data": data,
                "is_default": is_default,
            }


def upgrade() -> None:
    conn = op.get_bind()
    table = op.create_table(
        "dotfiles",
        sa.Column("id", sa.Uuid(), nullable=False, server_default=sa.text("uuid_generate_v7()")),
        sa.Column("entity_type", sa.String(32), nullable=False),
        sa.Column("entity_id", sa.Uuid(), nullable=False),
        sa.Column("path", sa.Text(), nullable=False),
        sa.Column("perm", sa.Text(), nullable=False),
        sa.Column("data", sa.Text(), nullable=False),
        sa.Column("is_default", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_dotfiles")),
        sa.ForeignKeyConstraint(
            ["entity_type", "entity_id"],
            ["virtual_entities.entity_type", "virtual_entities.entity_id"],
            name=op.f("fk_dotfiles_entity_type_virtual_entities"),
            ondelete="CASCADE",
        ),
        sa.CheckConstraint("char_length(perm) <= 4", name=op.f("ck_dotfiles_dotfile_perm_length")),
        sa.CheckConstraint(
            "char_length(data) <= 65536", name=op.f("ck_dotfiles_dotfile_data_length")
        ),
    )
    op.create_index(
        "uq_dotfiles_is_default",
        "dotfiles",
        ["entity_type", "entity_id", "path"],
        unique=True,
        postgresql_where=sa.text("is_default"),
    )
    keypairs = sa.table(
        "keypairs",
        sa.column("id"),
        sa.column("user"),
        sa.column("dotfiles"),
        sa.column("is_default"),
    )
    rows = _batched_rows(
        conn,
        sa.select(
            keypairs.c.id,
            keypairs.c.user.label("owner"),
            keypairs.c.dotfiles,
            keypairs.c.is_default,
        ),
    )
    for batch in batched(_unpack_dotfiles(rows), 1000):
        conn.execute(table.insert(), list(batch))
    op.drop_column("keypairs", "dotfiles")


def downgrade() -> None:
    conn = op.get_bind()
    op.add_column(
        "keypairs",
        sa.Column(
            "dotfiles",
            sa.LargeBinary(length=65536),
            nullable=False,
            server_default=sa.text("decode('90', 'hex')"),
        ),
    )
    table = sa.table(
        "dotfiles",
        sa.column("id"),
        sa.column("entity_id"),
        sa.column("entity_type"),
        sa.column("path"),
        sa.column("perm"),
        sa.column("data"),
        sa.column("is_default"),
    )
    rows = _batched_rows(
        conn,
        sa.select(
            table.c.id, table.c.entity_id.label("owner"), table.c.path, table.c.perm, table.c.data
        ).where(
            table.c.entity_type == "user",
            table.c.is_default,
        ),
    )
    updates = (
        {
            "owner": owner,
            "dotfiles": msgpack.packb(
                [{"path": row["path"], "perm": row["perm"], "data": row["data"]} for row in files],
                use_bin_type=True,
            ),
        }
        for owner, files in groupby(rows, key=lambda row: row["owner"])
    )
    for batch in batched(updates, 1000):
        conn.execute(
            sa.text('UPDATE keypairs SET dotfiles = :dotfiles WHERE "user" = :owner'), list(batch)
        )
    op.alter_column("keypairs", "dotfiles", server_default=None)
    op.drop_table("dotfiles")
