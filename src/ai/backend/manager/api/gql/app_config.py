"""GraphQL types and operations for app configuration."""

from __future__ import annotations

from typing import Any, cast

import strawberry
from strawberry import ID, Info

from ai.backend.common.contexts.user import current_user
from ai.backend.common.dto.manager.v2.app_config.request import (
    DeleteDomainConfigInput as DeleteDomainConfigInputDTO,
)
from ai.backend.common.dto.manager.v2.app_config.request import (
    DeleteUserConfigInput as DeleteUserConfigInputDTO,
)
from ai.backend.common.dto.manager.v2.app_config.request import (
    UpsertDomainConfigInput as UpsertDomainConfigInputDTO,
)
from ai.backend.common.dto.manager.v2.app_config.request import (
    UpsertUserConfigInput as UpsertUserConfigInputDTO,
)
from ai.backend.common.dto.manager.v2.app_config.response import (
    AppConfigNode,
    UpsertDomainConfigPayloadDTO,
    UpsertUserConfigPayloadDTO,
)
from ai.backend.common.dto.manager.v2.app_config.response import (
    DeleteDomainConfigPayload as DeleteDomainConfigPayloadDTO,
)
from ai.backend.common.dto.manager.v2.app_config.response import (
    DeleteUserConfigPayload as DeleteUserConfigPayloadDTO,
)
from ai.backend.manager.api.gql.decorators import (
    BackendAIGQLMeta,
    PydanticInputMixin,
    gql_mutation,
    gql_pydantic_input,
    gql_pydantic_type,
    gql_root_field,
)
from ai.backend.manager.api.gql.pydantic_compat import PydanticOutputMixin
from ai.backend.manager.api.gql.utils import check_admin_only, dedent_strip
from ai.backend.manager.errors.auth import InsufficientPrivilege

from .types import StrawberryGQLContext


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="25.16.0",
        description="App configuration data.",
    ),
    model=AppConfigNode,
)
class AppConfig(PydanticOutputMixin[AppConfigNode]):
    """GraphQL type for app configuration."""

    extra_config: strawberry.scalars.JSON


@gql_pydantic_input(
    BackendAIGQLMeta(
        description=dedent_strip("""\
            Input for creating or updating domain-level app configuration.
            The provided extra_config object will completely replace the existing configuration;
            existing keys not present in the new extra_config will be removed.
            All users in this domain will be affected by these settings when their configurations are merged.
        """),
        added_version="24.09.0",
    ),
)
class UpsertDomainConfigInput(PydanticInputMixin[UpsertDomainConfigInputDTO]):
    """Input type for upserting domain-level app configuration."""

    domain_name: str
    extra_config: strawberry.scalars.JSON


@gql_pydantic_input(
    BackendAIGQLMeta(
        description=dedent_strip("""\
            Input for creating or updating user-level app configuration.
            The provided extra_config object will completely replace the existing configuration;
            existing keys not present in the new extra_config will be removed.
            These settings will override domain-level settings when configurations are merged for this user.
            If user_id is not provided, the current user's configuration will be updated.
        """),
        added_version="24.09.0",
    ),
)
class UpsertUserConfigInput(PydanticInputMixin[UpsertUserConfigInputDTO]):
    """Input type for upserting user-level app configuration."""

    extra_config: strawberry.scalars.JSON
    user_id: ID | None = None


@gql_pydantic_input(
    BackendAIGQLMeta(
        description="Input for deleting domain-level app configuration", added_version="25.16.0"
    ),
)
class DeleteDomainConfigInput(PydanticInputMixin[DeleteDomainConfigInputDTO]):
    """Input type for deleting domain-level app configuration."""

    domain_name: str


@gql_pydantic_input(
    BackendAIGQLMeta(
        description=dedent_strip("""\
            Input for deleting user-level app configuration.
            If user_id is not provided, the current user's configuration will be deleted.
        """),
        added_version="24.09.0",
    ),
)
class DeleteUserConfigInput(PydanticInputMixin[DeleteUserConfigInputDTO]):
    """Input type for deleting user-level app configuration."""

    user_id: ID | None = None


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="25.16.0",
        description="Payload returned after upserting domain-level app configuration. Contains the resulting configuration that was stored.",
    ),
    model=UpsertDomainConfigPayloadDTO,
)
class UpsertDomainConfigPayload(PydanticOutputMixin[UpsertDomainConfigPayloadDTO]):
    """Payload returned after upserting domain-level app configuration."""

    app_config: AppConfig


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="25.16.0",
        description="Payload returned after upserting user-level app configuration. Contains the resulting configuration that was stored.",
    ),
    model=UpsertUserConfigPayloadDTO,
)
class UpsertUserConfigPayload(PydanticOutputMixin[UpsertUserConfigPayloadDTO]):
    """Payload returned after upserting user-level app configuration."""

    app_config: AppConfig


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="25.16.0",
        description="Payload returned after deleting domain-level app configuration. Indicates whether the deletion was successful.",
    ),
    model=DeleteDomainConfigPayloadDTO,
)
class DeleteDomainConfigPayload:
    """Payload returned after deleting domain-level app configuration."""

    deleted: strawberry.auto


@gql_pydantic_type(
    BackendAIGQLMeta(
        added_version="25.16.0",
        description="Payload returned after deleting user-level app configuration. Indicates whether the deletion was successful.",
    ),
    model=DeleteUserConfigPayloadDTO,
)
class DeleteUserConfigPayload:
    """Payload returned after deleting user-level app configuration."""

    deleted: strawberry.auto


@gql_root_field(
    BackendAIGQLMeta(
        added_version="26.2.0",
        description="Retrieve domain-level app configuration (admin only). Returns only the configuration set specifically for the domain, without merging. This query is useful for checking what values are configured at the domain level when you want to modify domain or user configurations separately. For actual configuration values to be applied, use mergedAppConfig instead.",
    )
)  # type: ignore[misc]
async def admin_domain_app_config(
    domain_name: str,
    info: Info[StrawberryGQLContext],
) -> AppConfig | None:
    """Get domain-level app configuration (admin only)."""
    check_admin_only()
    result = await info.context.adapters.app_config.get_domain_config(domain_name)
    if result is None:
        return None
    return AppConfig.from_pydantic(result)


@gql_root_field(
    BackendAIGQLMeta(
        added_version="25.16.0",
        description="Retrieve domain-level app configuration. Returns only the configuration set specifically for the domain, without merging. This query is useful for checking what values are configured at the domain level when you want to modify domain or user configurations separately. For actual configuration values to be applied, use mergedAppConfig instead. Requires admin privileges.",
    ),
    deprecation_reason="Use admin_domain_app_config instead. This API will be removed after v26.3.0. See BEP-1041 for migration guide.",
)  # type: ignore[misc]
async def domain_app_config(
    domain_name: str,
    info: Info[StrawberryGQLContext],
) -> AppConfig | None:
    """Get domain-level app configuration."""
    me = current_user()
    if me is None or not (me.is_admin or me.is_superadmin):
        raise InsufficientPrivilege("Admin privileges required to access domain configuration")

    result = await info.context.adapters.app_config.get_domain_config(domain_name)
    if result is None:
        return None
    return AppConfig.from_pydantic(result)


@gql_root_field(
    BackendAIGQLMeta(
        added_version="25.16.0",
        description="Retrieve user-level app configuration. Returns only the configuration set specifically for the user, without merging with domain config. This query is useful for checking what values are configured at the user level when you want to modify domain or user configurations separately. For actual configuration values to be applied, use mergedAppConfig instead. If user_id is not provided, returns the current user's configuration. Users can only access their own configuration, but admins can access any user's configuration.",
    )
)  # type: ignore[misc]
async def user_app_config(
    info: Info[StrawberryGQLContext],
    user_id: ID | None = None,
) -> AppConfig | None:
    """Get user-level app configuration."""
    me = current_user()
    if me is None:
        raise InsufficientPrivilege("Authentication required")

    # Use current user's ID if user_id is not provided
    target_user_id = str(user_id) if user_id is not None else str(me.user_id)

    if str(me.user_id) != target_user_id and not (me.is_admin or me.is_superadmin):
        raise InsufficientPrivilege("Cannot access another user's app configuration")

    result = await info.context.adapters.app_config.get_user_config(target_user_id)
    if result is None:
        return None
    return AppConfig.from_pydantic(result)


@gql_root_field(
    BackendAIGQLMeta(
        added_version="25.16.0",
        description="Retrieve merged app configuration for the current user. The result combines domain-level and user-level configurations, where user settings override domain settings for the same keys. This query should be used when working with user app configurations to get the actual configuration values that will be applied.",
    )
)  # type: ignore[misc]
async def merged_app_config(
    info: Info[StrawberryGQLContext],
) -> AppConfig:
    """Get merged app configuration for the current user."""
    me = current_user()
    if me is None:
        raise InsufficientPrivilege("Authentication required")

    result = await info.context.adapters.app_config.get_merged_config(str(me.user_id))
    return AppConfig.from_pydantic(result)


@gql_mutation(
    BackendAIGQLMeta(
        added_version="26.2.0",
        description="Create or update domain-level app configuration (admin only). The provided extra_config object will completely replace the existing configuration; existing keys not present in the new extra_config will be removed. All users in this domain will be affected by these settings when their configurations are merged, unless they have user-level configurations that override specific keys",
    ),
    name="adminUpsertDomainAppConfig",
)  # type: ignore[misc]
async def admin_upsert_domain_app_config(
    input: UpsertDomainConfigInput,
    info: Info[StrawberryGQLContext],
) -> UpsertDomainConfigPayload:
    """Create or update domain-level app configuration (admin only)."""
    check_admin_only()
    result = await info.context.adapters.app_config.upsert_domain_config(
        input.domain_name, cast(dict[str, Any], input.extra_config)
    )
    return UpsertDomainConfigPayload(app_config=AppConfig.from_pydantic(result))


@gql_mutation(
    BackendAIGQLMeta(
        added_version="25.16.0",
        description="Create or update domain-level app configuration. The provided extra_config object will completely replace the existing configuration; existing keys not present in the new extra_config will be removed. All users in this domain will be affected by these settings when their configurations are merged, unless they have user-level configurations that override specific keys. Requires admin privileges",
    ),
    name="upsertDomainAppConfig",
    deprecation_reason="Use admin_upsert_domain_app_config instead. This API will be removed after v26.3.0. See BEP-1041 for migration guide.",
)  # type: ignore[misc]
async def upsert_domain_app_config(
    input: UpsertDomainConfigInput,
    info: Info[StrawberryGQLContext],
) -> UpsertDomainConfigPayload:
    """Create or update domain-level app configuration."""
    me = current_user()
    if me is None or not (me.is_admin or me.is_superadmin):
        raise InsufficientPrivilege("Admin privileges required to modify domain configuration")

    result = await info.context.adapters.app_config.upsert_domain_config(
        input.domain_name, cast(dict[str, Any], input.extra_config)
    )
    return UpsertDomainConfigPayload(app_config=AppConfig.from_pydantic(result))


@gql_mutation(
    BackendAIGQLMeta(
        added_version="25.16.0",
        description="Create or update user-level app configuration. The provided extra_config object will completely replace the existing configuration; existing keys not present in the new extra_config will be removed. These settings will override domain-level settings when configurations are merged for this user. If user_id is not provided, the current user's configuration will be updated. Users can only modify their own configuration, but admins can modify any user's configuration",
    ),
    name="upsertUserAppConfig",
)  # type: ignore[misc]
async def upsert_user_app_config(
    input: UpsertUserConfigInput,
    info: Info[StrawberryGQLContext],
) -> UpsertUserConfigPayload:
    """Create or update user-level app configuration."""
    me = current_user()
    if me is None:
        raise InsufficientPrivilege("Authentication required")

    # Use current user's ID if user_id is not provided
    target_user_id = str(input.user_id) if input.user_id is not None else str(me.user_id)

    if str(me.user_id) != target_user_id and not (me.is_admin or me.is_superadmin):
        raise InsufficientPrivilege("Cannot modify another user's app configuration")

    result = await info.context.adapters.app_config.upsert_user_config(
        target_user_id, cast(dict[str, Any], input.extra_config)
    )
    return UpsertUserConfigPayload(app_config=AppConfig.from_pydantic(result))


@gql_mutation(
    BackendAIGQLMeta(
        added_version="26.2.0",
        description="Delete domain-level app configuration (admin only). All users in this domain may be affected by this deletion. After deletion, users will only receive their user-level configurations when configurations are merged, with no domain-level defaults",
    ),
    name="adminDeleteDomainAppConfig",
)  # type: ignore[misc]
async def admin_delete_domain_app_config(
    input: DeleteDomainConfigInput,
    info: Info[StrawberryGQLContext],
) -> DeleteDomainConfigPayload:
    """Delete domain-level app configuration (admin only)."""
    check_admin_only()
    result = await info.context.adapters.app_config.delete_domain_config(input.domain_name)
    return DeleteDomainConfigPayload(deleted=result.deleted)


@gql_mutation(
    BackendAIGQLMeta(
        added_version="25.16.0",
        description="Delete domain-level app configuration. All users in this domain may be affected by this deletion. After deletion, users will only receive their user-level configurations when configurations are merged, with no domain-level defaults. Requires admin privileges",
    ),
    name="deleteDomainAppConfig",
    deprecation_reason="Use admin_delete_domain_app_config instead. This API will be removed after v26.3.0. See BEP-1041 for migration guide.",
)  # type: ignore[misc]
async def delete_domain_app_config(
    input: DeleteDomainConfigInput,
    info: Info[StrawberryGQLContext],
) -> DeleteDomainConfigPayload:
    """Delete domain-level app configuration."""
    me = current_user()
    if me is None or not (me.is_admin or me.is_superadmin):
        raise InsufficientPrivilege("Admin privileges required to delete domain configuration")

    result = await info.context.adapters.app_config.delete_domain_config(input.domain_name)
    return DeleteDomainConfigPayload(deleted=result.deleted)


@gql_mutation(
    BackendAIGQLMeta(
        added_version="25.16.0",
        description="Delete user-level app configuration. After deletion, the user will still receive domain-level configuration values when configurations are merged, as domain settings remain unaffected. If user_id is not provided, the current user's configuration will be deleted. Users can only delete their own configuration, but admins can delete any user's configuration",
    ),
    name="deleteUserAppConfig",
)  # type: ignore[misc]
async def delete_user_app_config(
    input: DeleteUserConfigInput,
    info: Info[StrawberryGQLContext],
) -> DeleteUserConfigPayload:
    """Delete user-level app configuration."""
    me = current_user()
    if me is None:
        raise InsufficientPrivilege("Authentication required")

    # Use current user's ID if user_id is not provided
    target_user_id = str(input.user_id) if input.user_id is not None else str(me.user_id)

    if str(me.user_id) != target_user_id and not (me.is_admin or me.is_superadmin):
        raise InsufficientPrivilege("Cannot delete another user's app configuration")

    result = await info.context.adapters.app_config.delete_user_config(target_user_id)
    return DeleteUserConfigPayload(deleted=result.deleted)
