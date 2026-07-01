"""GraphQL login client type module."""

from .resolver import (
    admin_create_login_client_type,
    admin_delete_login_client_type,
    admin_update_login_client_type,
    login_client_type,
    login_client_types,
)
from .types import (
    CreateLoginClientTypeInputGQL,
    CreateLoginClientTypePayloadGQL,
    DeleteLoginClientTypePayloadGQL,
    LoginClientTypeConnection,
    LoginClientTypeEdge,
    LoginClientTypeFilterGQL,
    LoginClientTypeGQL,
    LoginClientTypeOrderByGQL,
    LoginClientTypeOrderFieldGQL,
    UpdateLoginClientTypeInputGQL,
    UpdateLoginClientTypePayloadGQL,
)

__all__ = (
    # Types
    "CreateLoginClientTypeInputGQL",
    "CreateLoginClientTypePayloadGQL",
    "DeleteLoginClientTypePayloadGQL",
    "LoginClientTypeConnection",
    "LoginClientTypeEdge",
    "LoginClientTypeFilterGQL",
    "LoginClientTypeGQL",
    "LoginClientTypeOrderByGQL",
    "LoginClientTypeOrderFieldGQL",
    "UpdateLoginClientTypeInputGQL",
    "UpdateLoginClientTypePayloadGQL",
    # Query resolvers
    "login_client_type",
    "login_client_types",
    # Mutation resolvers
    "admin_create_login_client_type",
    "admin_update_login_client_type",
    "admin_delete_login_client_type",
)
