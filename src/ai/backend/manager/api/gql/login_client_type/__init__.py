"""GraphQL login client type module."""

from .resolver import (
    create_login_client_type,
    delete_login_client_type,
    login_client_type,
    login_client_types,
    update_login_client_type,
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
    "create_login_client_type",
    "update_login_client_type",
    "delete_login_client_type",
)
