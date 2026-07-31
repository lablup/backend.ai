"""use resource group IDs for fair-share uniqueness

Revision ID: b988f01b17a1
Revises: 3f9a1c7b2e04
Create Date: 2026-07-20

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "b988f01b17a1"
down_revision = "3f9a1c7b2e04"
# Part of: NEXT_RELEASE_VERSION
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_unique_constraint(
        "uq_domain_fair_share_rg_id",
        "domain_fair_shares",
        ["resource_group_id", "domain_name"],
    )
    op.create_unique_constraint(
        "uq_project_fair_share_rg_id",
        "project_fair_shares",
        ["resource_group_id", "project_id"],
    )
    op.create_unique_constraint(
        "uq_user_fair_share_rg_id",
        "user_fair_shares",
        ["resource_group_id", "user_uuid", "project_id"],
    )
    op.create_unique_constraint(
        "uq_domain_usage_bucket_rg_id",
        "domain_usage_buckets",
        ["domain_name", "resource_group_id", "period_start"],
    )
    op.create_unique_constraint(
        "uq_project_usage_bucket_rg_id",
        "project_usage_buckets",
        ["project_id", "resource_group_id", "period_start"],
    )
    op.create_unique_constraint(
        "uq_user_usage_bucket_rg_id",
        "user_usage_buckets",
        ["user_uuid", "project_id", "resource_group_id", "period_start"],
    )
    op.create_index(
        "ix_kernel_usage_rg_id_period",
        "kernel_usage_records",
        ["resource_group_id", "period_start"],
    )

    op.drop_constraint("uq_domain_fair_share", "domain_fair_shares", type_="unique")
    op.drop_constraint("uq_project_fair_share", "project_fair_shares", type_="unique")
    op.drop_constraint("uq_user_fair_share", "user_fair_shares", type_="unique")
    op.drop_constraint("uq_domain_usage_bucket", "domain_usage_buckets", type_="unique")
    op.drop_constraint("uq_project_usage_bucket", "project_usage_buckets", type_="unique")
    op.drop_constraint("uq_user_usage_bucket", "user_usage_buckets", type_="unique")


def downgrade() -> None:
    op.create_unique_constraint(
        "uq_domain_fair_share",
        "domain_fair_shares",
        ["resource_group", "domain_name"],
    )
    op.create_unique_constraint(
        "uq_project_fair_share",
        "project_fair_shares",
        ["resource_group", "project_id"],
    )
    op.create_unique_constraint(
        "uq_user_fair_share",
        "user_fair_shares",
        ["resource_group", "user_uuid", "project_id"],
    )
    op.create_unique_constraint(
        "uq_domain_usage_bucket",
        "domain_usage_buckets",
        ["domain_name", "resource_group", "period_start"],
    )
    op.create_unique_constraint(
        "uq_project_usage_bucket",
        "project_usage_buckets",
        ["project_id", "resource_group", "period_start"],
    )
    op.create_unique_constraint(
        "uq_user_usage_bucket",
        "user_usage_buckets",
        ["user_uuid", "project_id", "resource_group", "period_start"],
    )

    op.drop_index("ix_kernel_usage_rg_id_period", table_name="kernel_usage_records")
    op.drop_constraint("uq_domain_fair_share_rg_id", "domain_fair_shares", type_="unique")
    op.drop_constraint("uq_project_fair_share_rg_id", "project_fair_shares", type_="unique")
    op.drop_constraint("uq_user_fair_share_rg_id", "user_fair_shares", type_="unique")
    op.drop_constraint(
        "uq_domain_usage_bucket_rg_id",
        "domain_usage_buckets",
        type_="unique",
    )
    op.drop_constraint(
        "uq_project_usage_bucket_rg_id",
        "project_usage_buckets",
        type_="unique",
    )
    op.drop_constraint(
        "uq_user_usage_bucket_rg_id",
        "user_usage_buckets",
        type_="unique",
    )
