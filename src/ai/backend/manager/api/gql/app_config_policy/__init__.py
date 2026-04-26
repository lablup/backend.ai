"""AppConfigPolicy GraphQL API package."""

from .resolver import (
    admin_bulk_create_app_config_policies,
    admin_bulk_purge_app_config_policies,
    admin_bulk_update_app_config_policies,
    app_config_policies,
    app_config_policy,
)
from .types import (
    AppConfigPolicyFilterGQL,
    AppConfigPolicyGQL,
    AppConfigPolicyOrderByGQL,
    AppConfigPolicyOrderFieldGQL,
)

__all__ = [
    # Queries
    "app_config_policy",
    "app_config_policies",
    # Bulk mutations (bulk-only)
    "admin_bulk_create_app_config_policies",
    "admin_bulk_update_app_config_policies",
    "admin_bulk_purge_app_config_policies",
    # Types
    "AppConfigPolicyGQL",
    "AppConfigPolicyFilterGQL",
    "AppConfigPolicyOrderByGQL",
    "AppConfigPolicyOrderFieldGQL",
]
