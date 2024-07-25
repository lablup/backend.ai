"""Make nullable project of groups.container_registry column

Revision ID: 5f4cdf6aec86
Revises: 59a622c31820
Create Date: 2024-07-25 07:34:00.345988

"""

# revision identifiers, used by Alembic.
revision = "5f4cdf6aec86"
down_revision = "59a622c31820"
branch_labels = None
depends_on = None


def upgrade():
    # Retrieve existing data
    # connection = op.get_bind()
    # result = connection.execute(sa.text("SELECT id, container_registry FROM groups"))
    # groups = result.fetchall()

    # # Update JSON structure
    # for group in groups:
    #     container_registry = group['container_registry']
    #     if container_registry is not None:
    #         if "project" not in container_registry:
    #             container_registry["project"] = None

    #         updated_container_registry = json.dumps(container_registry)
    #         connection.execute(
    #             sa.text("UPDATE groups SET container_registry = :container_registry WHERE id = :id"),
    #             {"container_registry": updated_container_registry, "id": group['id']}
    #         )

    # Alter column to set nullable
    # op.alter_column('groups', 'container_registry', existing_type=psql.JSON, nullable=True)
    pass


def downgrade():
    # Revert nullable change
    # op.alter_column('groups', 'container_registry', existing_type=psql.JSON, nullable=False)
    pass

    # # Retrieve existing data
    # connection = op.get_bind()
    # result = connection.execute(sa.text("SELECT id, container_registry FROM groups"))
    # groups = result.fetchall()

    # # Revert JSON structure
    # for group in groups:
    #     container_registry = group['container_registry']
    #     if container_registry is not None and container_registry.get("project") is None:
    #         del container_registry["project"]

    #         updated_container_registry = json.dumps(container_registry)
    #         connection.execute(
    #             sa.text("UPDATE groups SET container_registry = :container_registry WHERE id = :id"),
    #             {"container_registry": updated_container_registry, "id": group['id']}
    #         )
