import logging

from graphql.language import FieldNode
from graphql.validation import ValidationRule

from ai.backend.common.logging import BraceStyleAdapter

log = BraceStyleAdapter(logging.getLogger(__spec__.name))  # type: ignore[name-defined]

__all__ = ["GQLDeprecatedQueryValidator"]

deprecated_queries = (
    "agents",
    "domains",
    "groups_by_name",
    "groups",
    "images",
    "customized_images",
    "users",
    "keypairs",
    "keypair_resource_policies",
    "user_resource_policies",
    "resource_presets",
    "scaling_groups",
    "scaling_groups_for_domain",
    "scaling_groups_for_user_group",
    "scaling_groups_for_keypair",
    "vfolders",
    "container_registries",
)


def is_deprecated_query(query_name: str) -> bool:
    return query_name.lower() in deprecated_queries


class GQLDeprecatedQueryValidator(ValidationRule):
    def enter_field(self, node: FieldNode, *_args):
        field_name = node.name.value
        if is_deprecated_query(field_name):
            log.warning("Non-paginated query '{}' is being used.", field_name)
