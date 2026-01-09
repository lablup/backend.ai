"""GraphQL types and operations for app configuration."""

from __future__ import annotations

from typing import Optional

import strawberry
from strawberry import ID, Info

from ai.backend.common.contexts.user import current_user
from ai.backend.manager.api.gql.utils import dedent_strip
from ai.backend.manager.errors.auth import InsufficientPrivilege
from ai.backend.manager.repositories.app_config.updaters import AppConfigUpdaterSpec
from ai.backend.manager.services.app_config.actions import (
    DeleteDomainConfigAction,
    DeleteUserConfigAction,
    GetDomainConfigAction,
    GetMergedAppConfigAction,
    GetUserConfigAction,
    UpsertDomainConfigAction,
    UpsertUserConfigAction,
)
from ai.backend.manager.types import OptionalState

from .types import StrawberryGQLContext


@strawberry.type(description="Added in 25.16.0. App configuration data")
class AppConfig:
    """GraphQL type for app configuration."""

    extra_config: strawberry.scalars.JSON


@strawberry.input(
    description=dedent_strip(
        """\
        Added in 25.16.0.
        Input for creating or updating domain-level app configuration.
        The provided extra_config object will completely replace the existing configuration;
        existing keys not present in the new extra_config will be removed.
        All users in this domain will be affected by these settings when their configurations are merged.
        """
    )
)
class UpsertDomainConfigInput:
    """Input type for upserting domain-level app configuration."""

    domain_name: str
    extra_config: strawberry.scalars.JSON

    def to_updater_spec(self) -> AppConfigUpdaterSpec:
        return AppConfigUpdaterSpec(extra_config=OptionalState.update(self.extra_config))


@strawberry.input(
    description=dedent_strip(
        """\
        Added in 25.16.0.
        Input for creating or updating user-level app configuration.
        The provided extra_config object will completely replace the existing configuration;
        existing keys not present in the new extra_config will be removed.
        These settings will override domain-level settings when configurations are merged for this user.
        If user_id is not provided, the current user's configuration will be updated.
        """
    )
)
class UpsertUserConfigInput:
    """Input type for upserting user-level app configuration."""

    extra_config: strawberry.scalars.JSON
    user_id: Optional[ID] = None

    def to_updater_spec(self) -> AppConfigUpdaterSpec:
        return AppConfigUpdaterSpec(extra_config=OptionalState.update(self.extra_config))


@strawberry.input(description="Added in 25.16.0. Input for deleting domain-level app configuration")
class DeleteDomainConfigInput:
    """Input type for deleting domain-level app configuration."""

    domain_name: str


@strawberry.input(
    description=dedent_strip(
        """\
        Added in 25.16.0.
        Input for deleting user-level app configuration.
        If user_id is not provided, the current user's configuration will be deleted.
        """
    )
)
class DeleteUserConfigInput:
    """Input type for deleting user-level app configuration."""

    user_id: Optional[ID] = None


@strawberry.type(
    description=dedent_strip(
        """\
        Added in 25.16.0.
        Payload returned after upserting domain-level app configuration.
        Contains the resulting configuration that was stored.
        """
    )
)
class UpsertDomainConfigPayload:
    """Payload returned after upserting domain-level app configuration."""

    app_config: AppConfig


@strawberry.type(
    description=dedent_strip(
        """\
        Added in 25.16.0.
        Payload returned after upserting user-level app configuration.
        Contains the resulting configuration that was stored.
        """
    )
)
class UpsertUserConfigPayload:
    """Payload returned after upserting user-level app configuration."""

    app_config: AppConfig


@strawberry.type(
    description=dedent_strip(
        """\
        Added in 25.16.0.
        Payload returned after deleting domain-level app configuration.
        Indicates whether the deletion was successful.
        """
    )
)
class DeleteDomainConfigPayload:
    """Payload returned after deleting domain-level app configuration."""

    deleted: bool


@strawberry.type(
    description=dedent_strip(
        """\
        Added in 25.16.0.
        Payload returned after deleting user-level app configuration.
        Indicates whether the deletion was successful.
        """
    )
)
class DeleteUserConfigPayload:
    """Payload returned after deleting user-level app configuration."""

    deleted: bool


@strawberry.field(
    description=dedent_strip(
        """\
        Added in 25.16.0.
        Retrieve domain-level app configuration.
        Returns only the configuration set specifically for the domain, without merging.
        This query is useful for checking what values are configured at the domain level
        when you want to modify domain or user configurations separately.
        For actual configuration values to be applied, use mergedAppConfig instead.
        Requires admin privileges.
        """
    )
)
async def domain_app_config(
    domain_name: str,
    info: Info[StrawberryGQLContext],
) -> Optional[AppConfig]:
    """Get domain-level app configuration."""
    processors = info.context.processors
    me = current_user()
    if me is None or not (me.is_admin or me.is_superadmin):
        raise InsufficientPrivilege("Admin privileges required to access domain configuration")

    action_result = await processors.app_config.get_domain_config.wait_for_complete(
        GetDomainConfigAction(domain_name=domain_name)
    )

    if not action_result.result:
        return None

    return AppConfig(extra_config=action_result.result.extra_config)


@strawberry.field(
    description=dedent_strip(
        """\
        Added in 25.16.0.
        Retrieve user-level app configuration.
        Returns only the configuration set specifically for the user, without merging with domain config.
        This query is useful for checking what values are configured at the user level
        when you want to modify domain or user configurations separately.
        For actual configuration values to be applied, use mergedAppConfig instead.
        If user_id is not provided, returns the current user's configuration.
        Users can only access their own configuration, but admins can access any user's configuration.
        """
    )
)
async def user_app_config(
    info: Info[StrawberryGQLContext],
    user_id: Optional[ID] = None,
) -> Optional[AppConfig]:
    """Get user-level app configuration."""
    processors = info.context.processors
    me = current_user()
    if me is None:
        raise InsufficientPrivilege("Authentication required")

    # Use current user's ID if user_id is not provided
    target_user_id = str(user_id) if user_id is not None else str(me.user_id)

    if str(me.user_id) != target_user_id and not (me.is_admin or me.is_superadmin):
        raise InsufficientPrivilege("Cannot access another user's app configuration")

    action_result = await processors.app_config.get_user_config.wait_for_complete(
        GetUserConfigAction(user_id=target_user_id)
    )

    if not action_result.result:
        return None

    return AppConfig(extra_config=action_result.result.extra_config)


@strawberry.field(
    description=dedent_strip(
        """\
        Added in 25.16.0.
        Retrieve merged app configuration for the current user.
        The result combines domain-level and user-level configurations,
        where user settings override domain settings for the same keys.
        This query should be used when working with user app configurations
        to get the actual configuration values that will be applied.
        """
    )
)
async def merged_app_config(
    info: Info[StrawberryGQLContext],
) -> AppConfig:
    """Get merged app configuration for the current user."""
    processors = info.context.processors
    me = current_user()
    if me is None:
        raise InsufficientPrivilege("Authentication required")

    action_result = await processors.app_config.get_merged_config.wait_for_complete(
        GetMergedAppConfigAction(user_id=str(me.user_id))
    )

    return AppConfig(extra_config=action_result.merged_config)


@strawberry.mutation(
    name="upsertDomainAppConfig",
    description=dedent_strip(
        """\
        Added in 25.16.0.
        Create or update domain-level app configuration.
        The provided extra_config object will completely replace the existing configuration;
        existing keys not present in the new extra_config will be removed.
        All users in this domain will be affected by these settings when their configurations are merged,
        unless they have user-level configurations that override specific keys.
        Requires admin privileges.
        """
    ),
)
async def upsert_domain_app_config(
    input: UpsertDomainConfigInput,
    info: Info[StrawberryGQLContext],
) -> UpsertDomainConfigPayload:
    """Create or update domain-level app configuration."""
    processors = info.context.processors
    me = current_user()
    if me is None or not (me.is_admin or me.is_superadmin):
        raise InsufficientPrivilege("Admin privileges required to modify domain configuration")

    action_result = await processors.app_config.upsert_domain_config.wait_for_complete(
        UpsertDomainConfigAction(
            domain_name=input.domain_name,
            updater_spec=input.to_updater_spec(),
        )
    )

    return UpsertDomainConfigPayload(
        app_config=AppConfig(extra_config=action_result.result.extra_config)
    )


@strawberry.mutation(
    name="upsertUserAppConfig",
    description=dedent_strip(
        """\
        Added in 25.16.0.
        Create or update user-level app configuration.
        The provided extra_config object will completely replace the existing configuration;
        existing keys not present in the new extra_config will be removed.
        These settings will override domain-level settings when configurations are merged for this user.
        If user_id is not provided, the current user's configuration will be updated.
        Users can only modify their own configuration, but admins can modify any user's configuration.
        """
    ),
)
async def upsert_user_app_config(
    input: UpsertUserConfigInput,
    info: Info[StrawberryGQLContext],
) -> UpsertUserConfigPayload:
    """Create or update user-level app configuration."""
    processors = info.context.processors
    me = current_user()
    if me is None:
        raise InsufficientPrivilege("Authentication required")

    # Use current user's ID if user_id is not provided
    target_user_id = str(input.user_id) if input.user_id is not None else str(me.user_id)

    if str(me.user_id) != target_user_id and not (me.is_admin or me.is_superadmin):
        raise InsufficientPrivilege("Cannot modify another user's app configuration")

    action_result = await processors.app_config.upsert_user_config.wait_for_complete(
        UpsertUserConfigAction(
            user_id=target_user_id,
            updater_spec=input.to_updater_spec(),
        )
    )

    return UpsertUserConfigPayload(
        app_config=AppConfig(extra_config=action_result.result.extra_config)
    )


@strawberry.mutation(
    name="deleteDomainAppConfig",
    description=dedent_strip(
        """\
        Added in 25.16.0.
        Delete domain-level app configuration.
        All users in this domain may be affected by this deletion.
        After deletion, users will only receive their user-level configurations
        when configurations are merged, with no domain-level defaults.
        Requires admin privileges.
        """
    ),
)
async def delete_domain_app_config(
    input: DeleteDomainConfigInput,
    info: Info[StrawberryGQLContext],
) -> DeleteDomainConfigPayload:
    """Delete domain-level app configuration."""
    processors = info.context.processors
    me = current_user()
    if me is None or not (me.is_admin or me.is_superadmin):
        raise InsufficientPrivilege("Admin privileges required to delete domain configuration")

    action_result = await processors.app_config.delete_domain_config.wait_for_complete(
        DeleteDomainConfigAction(domain_name=input.domain_name)
    )

    return DeleteDomainConfigPayload(deleted=action_result.deleted)


@strawberry.mutation(
    name="deleteUserAppConfig",
    description=dedent_strip(
        """\
        Added in 25.16.0.
        Delete user-level app configuration.
        After deletion, the user will still receive domain-level configuration values
        when configurations are merged, as domain settings remain unaffected.
        If user_id is not provided, the current user's configuration will be deleted.
        Users can only delete their own configuration, but admins can delete any user's configuration.
        """
    ),
)
async def delete_user_app_config(
    input: DeleteUserConfigInput,
    info: Info[StrawberryGQLContext],
) -> DeleteUserConfigPayload:
    """Delete user-level app configuration."""
    processors = info.context.processors
    me = current_user()
    if me is None:
        raise InsufficientPrivilege("Authentication required")

    # Use current user's ID if user_id is not provided
    target_user_id = str(input.user_id) if input.user_id is not None else str(me.user_id)

    if str(me.user_id) != target_user_id and not (me.is_admin or me.is_superadmin):
        raise InsufficientPrivilege("Cannot delete another user's app configuration")

    action_result = await processors.app_config.delete_user_config.wait_for_complete(
        DeleteUserConfigAction(user_id=target_user_id)
    )

    return DeleteUserConfigPayload(deleted=action_result.deleted)
