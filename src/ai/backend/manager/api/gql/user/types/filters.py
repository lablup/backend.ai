"""User GraphQL filter and order-by types."""

from __future__ import annotations

from enum import StrEnum
from typing import Self

from ai.backend.common.dto.manager.v2.user.request import (
    KeypairNestedFilter,
    UserFilter,
    UserOrder,
)
from ai.backend.common.dto.manager.v2.user.types import (
    UserDomainFilter,
    UserProjectFilter,
    UserRoleFilter,
    UserStatusFilter,
)
from ai.backend.common.meta.meta import NEXT_RELEASE_VERSION
from ai.backend.manager.api.gql.base import (
    DateTimeFilter,
    IntArrayFilter,
    IntFilter,
    NullableDateTimeFilter,
    OrderDirection,
    StringFilter,
    UUIDFilter,
)
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    gql_added_field,
    gql_enum,
    gql_field,
    gql_pydantic_input,
)
from ai.backend.manager.api.gql.keypair.types.filters import KeypairFilterGQL
from ai.backend.manager.api.gql.pydantic_compat import PydanticInputMixin

from .enums import UserRoleEnumGQL, UserStatusEnumGQL


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Filter for UserStatusV2 enum fields. Supports equals, in, not_equals, and not_in operations.",
        added_version="26.2.0",
    ),
    name="UserStatusV2EnumFilter",
)
class UserStatusEnumFilterGQL(PydanticInputMixin[UserStatusFilter]):
    """Filter for user status enum fields."""

    equals: UserStatusEnumGQL | None = None
    in_: list[UserStatusEnumGQL] | None = gql_field(
        description="The in  field.", name="in", default=None
    )
    not_equals: UserStatusEnumGQL | None = None
    not_in: list[UserStatusEnumGQL] | None = None


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Filter for UserRoleV2 enum fields. Supports equals, in, not_equals, and not_in operations.",
        added_version="26.2.0",
    ),
    name="UserRoleV2EnumFilter",
)
class UserRoleEnumFilterGQL(PydanticInputMixin[UserRoleFilter]):
    """Filter for user role enum fields."""

    equals: UserRoleEnumGQL | None = None
    in_: list[UserRoleEnumGQL] | None = gql_field(
        description="The in  field.", name="in", default=None
    )
    not_equals: UserRoleEnumGQL | None = None
    not_in: list[UserRoleEnumGQL] | None = None


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Nested filter for the domain a user belongs to. Filters users whose domain matches all specified conditions.",
        added_version="26.2.0",
    ),
    name="UserDomainNestedFilter",
)
class UserDomainNestedFilterGQL(PydanticInputMixin[UserDomainFilter]):
    """Nested filter for domain of a user."""

    name: StringFilter | None = None
    is_active: bool | None = None


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Nested filter for projects a user belongs to. Filters users that belong to at least one project matching all specified conditions.",
        added_version="26.2.0",
    ),
    name="UserProjectNestedFilter",
)
class UserProjectNestedFilterGQL(PydanticInputMixin[UserProjectFilter]):
    """Nested filter for projects of a user."""

    name: StringFilter | None = None
    is_active: bool | None = None


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Filter users by conditions on the keypairs they own.",
        added_version=NEXT_RELEASE_VERSION,
    ),
    name="UserKeypairNestedFilter",
)
class UserKeypairNestedFilterGQL(PydanticInputMixin[KeypairNestedFilter]):
    exists: bool | None = gql_field(
        description=(
            "Matches users that own at least one keypair when true, and users owning "
            "none when false. Says nothing about what the keypairs hold."
        ),
        default=None,
    )
    some: KeypairFilterGQL | None = gql_field(
        description="Matches users with at least one keypair satisfying all conditions.",
        default=None,
    )
    every: KeypairFilterGQL | None = gql_field(
        description=(
            "Matches users whose every keypair satisfies all conditions "
            "(also true when the user has no keypair)."
        ),
        default=None,
    )
    none: KeypairFilterGQL | None = gql_field(
        description="Matches users with no keypair satisfying all conditions.",
        default=None,
    )


_NESTED_FILTER_DEPRECATION = (
    "Filter by the user's {subject}. Deprecated since "
    + NEXT_RELEASE_VERSION
    + ". The condition is evaluated on rows the caller may not be able to read. Use {instead}."
)


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Filter input for querying users. Supports filtering by UUID, username, email, status, domain, integration_name, role, creation time, and nested domain/project filters. Multiple filters can be combined using AND, OR, and NOT logical operators.",
        added_version="26.2.0",
    ),
    name="UserV2Filter",
)
class UserFilterGQL(PydanticInputMixin[UserFilter]):
    """Filter for user queries."""

    uuid: UUIDFilter | None = None
    username: StringFilter | None = None
    email: StringFilter | None = None
    full_name: StringFilter | None = gql_added_field(
        BackendAIGQLMeta(
            added_version="26.4.4",
            description="Filter by full name.",
        ),
        default=None,
    )
    description: StringFilter | None = gql_added_field(
        BackendAIGQLMeta(
            added_version="26.4.4",
            description="Filter by description.",
        ),
        default=None,
    )
    status: UserStatusEnumFilterGQL | None = None
    status_info: StringFilter | None = gql_added_field(
        BackendAIGQLMeta(
            added_version="26.4.4",
            description="Filter by status info detail.",
        ),
        default=None,
    )
    domain_name: StringFilter | None = None
    domain_id: UUIDFilter | None = gql_added_field(
        BackendAIGQLMeta(
            added_version=NEXT_RELEASE_VERSION,
            description="Filter by domain ID.",
        ),
        default=None,
    )
    integration_name: StringFilter | None = gql_added_field(
        BackendAIGQLMeta(
            added_version="26.4.2",
            description="Filter by external integration identifier.",
        ),
        default=None,
    )
    resource_policy: StringFilter | None = gql_added_field(
        BackendAIGQLMeta(
            added_version="26.4.4",
            description="Filter by user resource policy name.",
        ),
        default=None,
    )
    role: UserRoleEnumFilterGQL | None = None
    need_password_change: bool | None = gql_added_field(
        BackendAIGQLMeta(
            added_version="26.4.4",
            description="Filter by whether a password change is required.",
        ),
        default=None,
    )
    totp_activated: bool | None = gql_added_field(
        BackendAIGQLMeta(
            added_version="26.4.4",
            description="Filter by whether TOTP two-factor auth is activated.",
        ),
        default=None,
    )
    sudo_session_enabled: bool | None = gql_added_field(
        BackendAIGQLMeta(
            added_version="26.4.4",
            description="Filter by whether sudo sessions are enabled.",
        ),
        default=None,
    )
    container_uid: IntFilter | None = gql_added_field(
        BackendAIGQLMeta(
            added_version="26.4.4",
            description="Filter by container UID.",
        ),
        default=None,
    )
    container_main_gid: IntFilter | None = gql_added_field(
        BackendAIGQLMeta(
            added_version="26.4.4",
            description="Filter by container main GID.",
        ),
        default=None,
    )
    container_gids: IntArrayFilter | None = gql_added_field(
        BackendAIGQLMeta(
            added_version="26.4.4",
            description="Filter by container supplementary GIDs.",
        ),
        default=None,
    )
    created_at: DateTimeFilter | None = None
    modified_at: DateTimeFilter | None = gql_added_field(
        BackendAIGQLMeta(
            added_version=NEXT_RELEASE_VERSION,
            description="Filter by last modification timestamp.",
        ),
        default=None,
    )
    totp_activated_at: NullableDateTimeFilter | None = gql_added_field(
        BackendAIGQLMeta(
            added_version=NEXT_RELEASE_VERSION,
            description="Filter by when TOTP two-factor auth was activated.",
        ),
        default=None,
    )
    keypairs: UserKeypairNestedFilterGQL | None = gql_added_field(
        BackendAIGQLMeta(
            added_version=NEXT_RELEASE_VERSION,
            description="Filter by conditions on the user's keypairs.",
        ),
        default=None,
    )
    domain: UserDomainNestedFilterGQL | None = gql_field(
        description=_NESTED_FILTER_DEPRECATION.format(
            subject="domain", instead="the `domainName` filter, or look the domain up first"
        ),
        default=None,
    )
    project: UserProjectNestedFilterGQL | None = gql_field(
        description=_NESTED_FILTER_DEPRECATION.format(
            subject="projects",
            instead="`projectUsersV2`, which reads the users of one project",
        ),
        default=None,
    )
    AND: list[Self] | None = None
    OR: list[Self] | None = None
    NOT: list[Self] | None = None


_PROJECT_NAME_ORDER_DEPRECATION = (
    f"Deprecated since {NEXT_RELEASE_VERSION}. A user belongs to many projects, so this"
    " order folds them into a single name. Narrow the results with the `project` filter"
    " instead."
)


@gql_enum(
    BackendAIGQLMeta(
        added_version="26.2.0",
        description=(
            "Fields available for ordering user query results. "
            f"Added in {NEXT_RELEASE_VERSION}: ENTITY_ID, FULL_NAME, DESCRIPTION, STATUS_INFO, "
            "ROLE, DOMAIN_ID, INTEGRATION_NAME, RESOURCE_POLICY, NEED_PASSWORD_CHANGE, TOTP_ACTIVATED, "
            "TOTP_ACTIVATED_AT, SUDO_SESSION_ENABLED, CONTAINER_UID, CONTAINER_MAIN_GID. "
            "Each value orders by the user column of the same name; ENTITY_ID orders by the "
            "user's own id and PROJECT_NAME folds the projects the user is on."
        ),
    ),
    name="UserV2OrderField",
    deprecated_values={"PROJECT_NAME": _PROJECT_NAME_ORDER_DEPRECATION},
)
class UserOrderFieldGQL(StrEnum):
    ENTITY_ID = "entity_id"
    CREATED_AT = "created_at"
    MODIFIED_AT = "modified_at"
    USERNAME = "username"
    EMAIL = "email"
    FULL_NAME = "full_name"
    DESCRIPTION = "description"
    STATUS = "status"
    STATUS_INFO = "status_info"
    ROLE = "role"
    DOMAIN_NAME = "domain_name"
    DOMAIN_ID = "domain_id"
    INTEGRATION_NAME = "integration_name"
    RESOURCE_POLICY = "resource_policy"
    NEED_PASSWORD_CHANGE = "need_password_change"
    TOTP_ACTIVATED = "totp_activated"
    TOTP_ACTIVATED_AT = "totp_activated_at"
    SUDO_SESSION_ENABLED = "sudo_session_enabled"
    CONTAINER_UID = "container_uid"
    CONTAINER_MAIN_GID = "container_main_gid"
    PROJECT_NAME = "project_name"


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Specifies ordering for user query results. Combine field selection with direction to sort results. Default direction is DESC (descending).",
        added_version="26.2.0",
    ),
    name="UserV2OrderBy",
)
class UserOrderByGQL(PydanticInputMixin[UserOrder]):
    """OrderBy for user queries."""

    field: UserOrderFieldGQL = UserOrderFieldGQL.CREATED_AT
    direction: OrderDirection = OrderDirection.DESC
