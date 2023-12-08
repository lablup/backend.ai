"""stringify_userid

Revision ID: f8a71c3bffa2
Revises: bf4bae8f942e
Create Date: 2018-06-17 13:52:13.346856

"""

import os

import sqlalchemy as sa
from alembic import op

from ai.backend.manager.models.base import convention

# revision identifiers, used by Alembic.
revision = "f8a71c3bffa2"
down_revision = "bf4bae8f942e"
branch_labels = None
depends_on = None


def upgrade():
    metadata = sa.MetaData(naming_convention=convention)
    keypairs = sa.Table(
        "keypairs",
        metadata,
        sa.Column("user_id", sa.String(length=256), index=True),
    )

    print("Choose keypairs.user_id column migrate option:")
    print(" [a] Convert all numeric user IDs to strings directly")
    print(
        " [b] Convert numeric user IDs to strings using a mapping table\n"
        "     (user_id_map.txt must be present in the current working directory\n"
        "      which contains a space-sep.list of numeric and string ID pairs.)"
    )
    print("NOTE: If you choose [b], you will not be able to downgrade!")

    choice = os.environ.get("STRINGIFY_USERID_CHOICE")
    if choice is None:
        while True:
            choice = input("Your choice? [a/b] ")
            if choice in ("a", "b"):
                break
            print("Invalid choice.")
            continue

    op.alter_column("keypairs", "user_id", existing_type=sa.Integer(), type_=sa.String(length=256))

    # NOTE: We do the data migration after converting column type.

    if choice == "b":
        # query all unique user ids
        q = sa.select([keypairs.c.user_id]).group_by(keypairs.c.user_id)
        rows = op.get_bind().execute(q)
        user_ids = set(int(row.user_id) for row in rows)
        print(f"There are {len(user_ids)} unique user IDs.")

        user_id_map = {}
        with open("user_id_map.txt", "r") as f:
            for line in f:
                num_id, str_id = line.split(maxsplit=1)
                assert len(str_id) <= 256, f"Too long target user ID! ({num_id} -> {str_id!r})"
                user_id_map[int(num_id)] = str_id

        map_diff = user_ids - set(user_id_map.keys())
        assert len(map_diff) == 0, f"There are unmapped user IDs!\n{map_diff}"

        for num_id, str_id in user_id_map.items():
            op.execute(
                keypairs.update()
                .values({"user_id": str_id})
                .where(keypairs.c.user_id == str(num_id))
            )


def downgrade():
    op.alter_column("keypairs", "user_id", existing_type=sa.Integer(), type_=sa.String(length=256))
