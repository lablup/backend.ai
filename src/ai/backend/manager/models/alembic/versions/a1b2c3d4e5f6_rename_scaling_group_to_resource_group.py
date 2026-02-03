"""rename_scaling_group_to_resource_group

Revision ID: a1b2c3d4e5f6
Revises: f8a9b3c2d1e0
Create Date: 2026-01-15 10:00:00.000000

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "a1b2c3d4e5f6"
down_revision = "f8a9b3c2d1e0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Rename columns in all fair_share and resource_usage tables
    # scaling_group → resource_group

    # === domain_fair_shares ===
    # Drop indexes that reference scaling_group
    op.drop_index("ix_domain_fair_shares_scaling_group", table_name="domain_fair_shares")
    op.drop_index("ix_domain_fair_share_lookup", table_name="domain_fair_shares")
    # Drop unique constraint
    op.drop_constraint("uq_domain_fair_share", table_name="domain_fair_shares", type_="unique")
    # Rename column
    op.alter_column("domain_fair_shares", "scaling_group", new_column_name="resource_group")
    # Recreate indexes with new column name
    op.create_index(
        op.f("ix_domain_fair_shares_resource_group"),
        "domain_fair_shares",
        ["resource_group"],
        unique=False,
    )
    op.create_index(
        "ix_domain_fair_share_lookup",
        "domain_fair_shares",
        ["resource_group", "domain_name"],
        unique=False,
    )
    # Recreate unique constraint
    op.create_unique_constraint(
        "uq_domain_fair_share", "domain_fair_shares", ["resource_group", "domain_name"]
    )

    # === project_fair_shares ===
    op.drop_index("ix_project_fair_shares_scaling_group", table_name="project_fair_shares")
    op.drop_index("ix_project_fair_share_lookup", table_name="project_fair_shares")
    op.drop_constraint("uq_project_fair_share", table_name="project_fair_shares", type_="unique")
    op.alter_column("project_fair_shares", "scaling_group", new_column_name="resource_group")
    op.create_index(
        op.f("ix_project_fair_shares_resource_group"),
        "project_fair_shares",
        ["resource_group"],
        unique=False,
    )
    op.create_index(
        "ix_project_fair_share_lookup",
        "project_fair_shares",
        ["resource_group", "project_id"],
        unique=False,
    )
    op.create_unique_constraint(
        "uq_project_fair_share", "project_fair_shares", ["resource_group", "project_id"]
    )

    # === user_fair_shares ===
    op.drop_index("ix_user_fair_shares_scaling_group", table_name="user_fair_shares")
    op.drop_index("ix_user_fair_share_lookup", table_name="user_fair_shares")
    op.drop_constraint("uq_user_fair_share", table_name="user_fair_shares", type_="unique")
    op.alter_column("user_fair_shares", "scaling_group", new_column_name="resource_group")
    op.create_index(
        op.f("ix_user_fair_shares_resource_group"),
        "user_fair_shares",
        ["resource_group"],
        unique=False,
    )
    op.create_index(
        "ix_user_fair_share_lookup",
        "user_fair_shares",
        ["resource_group", "user_uuid", "project_id"],
        unique=False,
    )
    op.create_unique_constraint(
        "uq_user_fair_share", "user_fair_shares", ["resource_group", "user_uuid", "project_id"]
    )

    # === domain_usage_buckets ===
    op.drop_index("ix_domain_usage_bucket_lookup", table_name="domain_usage_buckets")
    op.drop_constraint("uq_domain_usage_bucket", table_name="domain_usage_buckets", type_="unique")
    op.alter_column("domain_usage_buckets", "scaling_group", new_column_name="resource_group")
    op.create_index(
        "ix_domain_usage_bucket_lookup",
        "domain_usage_buckets",
        ["domain_name", "resource_group", "period_start"],
        unique=False,
    )
    op.create_unique_constraint(
        "uq_domain_usage_bucket",
        "domain_usage_buckets",
        ["domain_name", "resource_group", "period_start"],
    )

    # === project_usage_buckets ===
    op.drop_index("ix_project_usage_bucket_lookup", table_name="project_usage_buckets")
    op.drop_constraint(
        "uq_project_usage_bucket", table_name="project_usage_buckets", type_="unique"
    )
    op.alter_column("project_usage_buckets", "scaling_group", new_column_name="resource_group")
    op.create_index(
        "ix_project_usage_bucket_lookup",
        "project_usage_buckets",
        ["project_id", "resource_group", "period_start"],
        unique=False,
    )
    op.create_unique_constraint(
        "uq_project_usage_bucket",
        "project_usage_buckets",
        ["project_id", "resource_group", "period_start"],
    )

    # === user_usage_buckets ===
    op.drop_index("ix_user_usage_bucket_lookup", table_name="user_usage_buckets")
    op.drop_constraint("uq_user_usage_bucket", table_name="user_usage_buckets", type_="unique")
    op.alter_column("user_usage_buckets", "scaling_group", new_column_name="resource_group")
    op.create_index(
        "ix_user_usage_bucket_lookup",
        "user_usage_buckets",
        ["user_uuid", "project_id", "resource_group", "period_start"],
        unique=False,
    )
    op.create_unique_constraint(
        "uq_user_usage_bucket",
        "user_usage_buckets",
        ["user_uuid", "project_id", "resource_group", "period_start"],
    )

    # === kernel_usage_records ===
    op.drop_index("ix_kernel_usage_records_scaling_group", table_name="kernel_usage_records")
    op.drop_index("ix_kernel_usage_sg_period", table_name="kernel_usage_records")
    op.alter_column("kernel_usage_records", "scaling_group", new_column_name="resource_group")
    op.create_index(
        op.f("ix_kernel_usage_records_resource_group"),
        "kernel_usage_records",
        ["resource_group"],
        unique=False,
    )
    op.create_index(
        "ix_kernel_usage_rg_period",
        "kernel_usage_records",
        ["resource_group", "period_start"],
        unique=False,
    )


def downgrade() -> None:
    # Reverse all changes: resource_group → scaling_group

    # === kernel_usage_records ===
    op.drop_index("ix_kernel_usage_rg_period", table_name="kernel_usage_records")
    op.drop_index("ix_kernel_usage_records_resource_group", table_name="kernel_usage_records")
    op.alter_column("kernel_usage_records", "resource_group", new_column_name="scaling_group")
    op.create_index(
        "ix_kernel_usage_sg_period",
        "kernel_usage_records",
        ["scaling_group", "period_start"],
        unique=False,
    )
    op.create_index(
        op.f("ix_kernel_usage_records_scaling_group"),
        "kernel_usage_records",
        ["scaling_group"],
        unique=False,
    )

    # === user_usage_buckets ===
    op.drop_constraint("uq_user_usage_bucket", table_name="user_usage_buckets", type_="unique")
    op.drop_index("ix_user_usage_bucket_lookup", table_name="user_usage_buckets")
    op.alter_column("user_usage_buckets", "resource_group", new_column_name="scaling_group")
    op.create_index(
        "ix_user_usage_bucket_lookup",
        "user_usage_buckets",
        ["user_uuid", "project_id", "scaling_group", "period_start"],
        unique=False,
    )
    op.create_unique_constraint(
        "uq_user_usage_bucket",
        "user_usage_buckets",
        ["user_uuid", "project_id", "scaling_group", "period_start"],
    )

    # === project_usage_buckets ===
    op.drop_constraint(
        "uq_project_usage_bucket", table_name="project_usage_buckets", type_="unique"
    )
    op.drop_index("ix_project_usage_bucket_lookup", table_name="project_usage_buckets")
    op.alter_column("project_usage_buckets", "resource_group", new_column_name="scaling_group")
    op.create_index(
        "ix_project_usage_bucket_lookup",
        "project_usage_buckets",
        ["project_id", "scaling_group", "period_start"],
        unique=False,
    )
    op.create_unique_constraint(
        "uq_project_usage_bucket",
        "project_usage_buckets",
        ["project_id", "scaling_group", "period_start"],
    )

    # === domain_usage_buckets ===
    op.drop_constraint("uq_domain_usage_bucket", table_name="domain_usage_buckets", type_="unique")
    op.drop_index("ix_domain_usage_bucket_lookup", table_name="domain_usage_buckets")
    op.alter_column("domain_usage_buckets", "resource_group", new_column_name="scaling_group")
    op.create_index(
        "ix_domain_usage_bucket_lookup",
        "domain_usage_buckets",
        ["domain_name", "scaling_group", "period_start"],
        unique=False,
    )
    op.create_unique_constraint(
        "uq_domain_usage_bucket",
        "domain_usage_buckets",
        ["domain_name", "scaling_group", "period_start"],
    )

    # === user_fair_shares ===
    op.drop_constraint("uq_user_fair_share", table_name="user_fair_shares", type_="unique")
    op.drop_index("ix_user_fair_share_lookup", table_name="user_fair_shares")
    op.drop_index("ix_user_fair_shares_resource_group", table_name="user_fair_shares")
    op.alter_column("user_fair_shares", "resource_group", new_column_name="scaling_group")
    op.create_index(
        "ix_user_fair_share_lookup",
        "user_fair_shares",
        ["scaling_group", "user_uuid", "project_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_user_fair_shares_scaling_group"),
        "user_fair_shares",
        ["scaling_group"],
        unique=False,
    )
    op.create_unique_constraint(
        "uq_user_fair_share", "user_fair_shares", ["scaling_group", "user_uuid", "project_id"]
    )

    # === project_fair_shares ===
    op.drop_constraint("uq_project_fair_share", table_name="project_fair_shares", type_="unique")
    op.drop_index("ix_project_fair_share_lookup", table_name="project_fair_shares")
    op.drop_index("ix_project_fair_shares_resource_group", table_name="project_fair_shares")
    op.alter_column("project_fair_shares", "resource_group", new_column_name="scaling_group")
    op.create_index(
        "ix_project_fair_share_lookup",
        "project_fair_shares",
        ["scaling_group", "project_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_project_fair_shares_scaling_group"),
        "project_fair_shares",
        ["scaling_group"],
        unique=False,
    )
    op.create_unique_constraint(
        "uq_project_fair_share", "project_fair_shares", ["scaling_group", "project_id"]
    )

    # === domain_fair_shares ===
    op.drop_constraint("uq_domain_fair_share", table_name="domain_fair_shares", type_="unique")
    op.drop_index("ix_domain_fair_share_lookup", table_name="domain_fair_shares")
    op.drop_index("ix_domain_fair_shares_resource_group", table_name="domain_fair_shares")
    op.alter_column("domain_fair_shares", "resource_group", new_column_name="scaling_group")
    op.create_index(
        "ix_domain_fair_share_lookup",
        "domain_fair_shares",
        ["scaling_group", "domain_name"],
        unique=False,
    )
    op.create_index(
        op.f("ix_domain_fair_shares_scaling_group"),
        "domain_fair_shares",
        ["scaling_group"],
        unique=False,
    )
    op.create_unique_constraint(
        "uq_domain_fair_share", "domain_fair_shares", ["scaling_group", "domain_name"]
    )
