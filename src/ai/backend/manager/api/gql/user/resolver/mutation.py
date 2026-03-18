"""User GraphQL mutation resolvers."""

from __future__ import annotations

import ipaddress
from typing import cast
from uuid import UUID

import strawberry
from strawberry import Info

from ai.backend.common.api_handlers import Sentinel
from ai.backend.common.contexts.client_ip import current_client_ip
from ai.backend.common.contexts.user import current_user
from ai.backend.common.exception import InvalidIpAddressValue, UnreachableError
from ai.backend.common.types import ReadableCIDR
from ai.backend.manager.api.gql.types import StrawberryGQLContext
from ai.backend.manager.api.gql.user.types import (
    BulkCreateUsersV2PayloadGQL,
    BulkCreateUserV2ErrorGQL,
    BulkCreateUserV2InputGQL,
    BulkPurgeUsersV2InputGQL,
    BulkPurgeUsersV2PayloadGQL,
    BulkPurgeUserV2ErrorGQL,
    BulkUpdateUsersV2PayloadGQL,
    BulkUpdateUserV2ErrorGQL,
    BulkUpdateUserV2InputGQL,
    CreateUserInputGQL,
    CreateUserPayloadGQL,
    DeleteUserPayloadGQL,
    DeleteUsersInputGQL,
    DeleteUsersPayloadGQL,
    PurgeUserInputGQL,
    PurgeUserPayloadGQL,
    UpdateMyAllowedClientIPInputGQL,
    UpdateMyAllowedClientIPPayloadGQL,
    UpdateUserPayloadGQL,
    UpdateUserV2InputGQL,
    UserV2GQL,
)
from ai.backend.manager.api.gql.utils import check_admin_only
from ai.backend.manager.data.user.types import UserStatus
from ai.backend.manager.errors.api import InvalidAPIParameters
from ai.backend.manager.models.hasher.types import PasswordInfo
from ai.backend.manager.models.user import UserRole
from ai.backend.manager.repositories.base.creator import Creator
from ai.backend.manager.repositories.base.updater import Updater
from ai.backend.manager.repositories.user.creators import UserCreatorSpec
from ai.backend.manager.repositories.user.updaters import UserUpdaterSpec
from ai.backend.manager.services.user.actions.create_user import (
    BulkCreateUserAction,
    UserCreateSpec,
)
from ai.backend.manager.services.user.actions.get_user import GetUserAction
from ai.backend.manager.services.user.actions.modify_user import (
    BulkModifyUserAction,
    ModifyUserAction,
    UserUpdateSpec,
)
from ai.backend.manager.services.user.actions.purge_user import BulkPurgeUserAction
from ai.backend.manager.types import OptionalState, TriState

# Create Mutations


@strawberry.mutation(
    description=(
        "Added in 26.2.0. Create a new user (admin only). "
        "Requires superadmin privileges. "
        "Automatically creates a default keypair for the user."
    )
)  # type: ignore[misc]
async def admin_create_user_v2(
    info: Info[StrawberryGQLContext],
    input: CreateUserInputGQL,
) -> CreateUserPayloadGQL:
    """Create a new user.

    Args:
        info: Strawberry GraphQL context.
        input: User creation input.

    Returns:
        CreateUserPayloadGQL with the created user.

    Raises:
        NotImplementedError: This mutation is not yet implemented.
    """
    check_admin_only()
    raise NotImplementedError("admin_create_user_v2 is not yet implemented")


@strawberry.mutation(
    description=(
        "Added in 26.2.0. Create multiple users in bulk (admin only). "
        "Requires superadmin privileges. "
        "Each user has individual specifications."
    )
)  # type: ignore[misc]
async def admin_bulk_create_users_v2(
    info: Info[StrawberryGQLContext],
    input: BulkCreateUserV2InputGQL,
) -> BulkCreateUsersV2PayloadGQL:
    """Create multiple users in bulk with individual specifications.

    Args:
        info: Strawberry GraphQL context.
        input: Bulk user creation input with individual specs.

    Returns:
        BulkCreateUsersV2PayloadGQL with created users.
    """
    check_admin_only()
    ctx = info.context
    auth_config = ctx.config_provider.config.auth

    # Build list of UserCreateSpec from input
    items: list[UserCreateSpec] = []
    for user_input in input.users:
        dto = user_input.to_pydantic()
        password_info = PasswordInfo(
            password=dto.password,
            algorithm=auth_config.password_hash_algorithm,
            rounds=auth_config.password_hash_rounds,
            salt_size=auth_config.password_hash_salt_size,
        )

        spec = UserCreatorSpec(
            email=dto.email,
            username=dto.username,
            password=password_info,
            need_password_change=dto.need_password_change,
            domain_name=dto.domain_name,
            full_name=dto.full_name,
            description=dto.description,
            status=UserStatus(dto.status),
            role=str(dto.role),
            allowed_client_ip=dto.allowed_client_ip,
            totp_activated=dto.totp_activated,
            resource_policy=dto.resource_policy,
            sudo_session_enabled=dto.sudo_session_enabled,
            container_uid=dto.container_uid,
            container_main_gid=dto.container_main_gid,
            container_gids=dto.container_gids,
        )

        group_ids = [str(gid) for gid in dto.group_ids] if dto.group_ids else None
        items.append(UserCreateSpec(creator=Creator(spec=spec), group_ids=group_ids))

    action = BulkCreateUserAction(items=items)
    result = await ctx.processors.user.bulk_create_users.wait_for_complete(action)

    created_users = [UserV2GQL.from_data(user_data) for user_data in result.data.successes]
    failed = [
        BulkCreateUserV2ErrorGQL(
            index=error.index,
            username=cast(UserCreatorSpec, error.spec).username,
            email=cast(UserCreatorSpec, error.spec).email,
            message=str(error.exception),
        )
        for error in result.data.failures
    ]

    return BulkCreateUsersV2PayloadGQL(
        created_users=created_users,
        failed=failed,
    )


# Update Mutations


@strawberry.mutation(
    description=(
        "Added in 26.3.0. Update a user's information (admin only). "
        "Requires superadmin privileges. "
        "Only provided fields will be updated."
    )
)  # type: ignore[misc]
async def admin_update_user_v2(
    info: Info[StrawberryGQLContext],
    user_id: UUID,
    input: UpdateUserV2InputGQL,
) -> UpdateUserPayloadGQL:
    """Update a user's information.

    Args:
        info: Strawberry GraphQL context.
        user_id: UUID of the user to update.
        input: User update input with fields to modify.

    Returns:
        UpdateUserPayloadGQL with the updated user.

    Raises:
        NotImplementedError: This mutation is not yet implemented.
    """
    check_admin_only()
    raise NotImplementedError("admin_update_user_v2 is not yet implemented")


@strawberry.mutation(
    description=(
        "Added in 26.3.0. Update multiple users in bulk (admin only). "
        "Requires superadmin privileges. "
        "Each user has individual update specifications."
    )
)  # type: ignore[misc]
async def admin_bulk_update_users_v2(
    info: Info[StrawberryGQLContext],
    input: BulkUpdateUserV2InputGQL,
) -> BulkUpdateUsersV2PayloadGQL:
    """Update multiple users in bulk with individual specifications.

    Args:
        info: Strawberry GraphQL context.
        input: Bulk user update input with individual specs.

    Returns:
        BulkUpdateUsersPayloadGQL with updated users and failures.
    """
    check_admin_only()
    ctx = info.context
    auth_config = ctx.config_provider.config.auth

    items: list[UserUpdateSpec] = []
    for user_item in input.users:
        dto = user_item.input.to_pydantic()

        updater_spec = UserUpdaterSpec(
            username=(
                OptionalState.update(dto.username)
                if dto.username is not None
                else OptionalState.nop()
            ),
            password=(
                OptionalState.update(
                    PasswordInfo(
                        password=dto.password,
                        algorithm=auth_config.password_hash_algorithm,
                        rounds=auth_config.password_hash_rounds,
                        salt_size=auth_config.password_hash_salt_size,
                    )
                )
                if dto.password is not None
                else OptionalState.nop()
            ),
            need_password_change=(
                OptionalState.update(dto.need_password_change)
                if dto.need_password_change is not None
                else OptionalState.nop()
            ),
            full_name=(
                OptionalState.nop()
                if isinstance(dto.full_name, Sentinel) or dto.full_name is None
                else OptionalState.update(dto.full_name)
            ),
            description=(
                OptionalState.nop()
                if isinstance(dto.description, Sentinel) or dto.description is None
                else OptionalState.update(dto.description)
            ),
            status=(
                OptionalState.update(UserStatus(dto.status))
                if dto.status is not None
                else OptionalState.nop()
            ),
            domain_name=(
                OptionalState.update(dto.domain_name)
                if dto.domain_name is not None
                else OptionalState.nop()
            ),
            role=(
                OptionalState.update(UserRole(dto.role))
                if dto.role is not None
                else OptionalState.nop()
            ),
            allowed_client_ip=(
                TriState.nop()
                if isinstance(dto.allowed_client_ip, Sentinel)
                else TriState.from_graphql(dto.allowed_client_ip)
            ),
            resource_policy=(
                OptionalState.update(dto.resource_policy)
                if dto.resource_policy is not None
                else OptionalState.nop()
            ),
            sudo_session_enabled=(
                OptionalState.update(dto.sudo_session_enabled)
                if dto.sudo_session_enabled is not None
                else OptionalState.nop()
            ),
            main_access_key=(
                TriState.nop()
                if isinstance(dto.main_access_key, Sentinel)
                else TriState.from_graphql(dto.main_access_key)
            ),
            container_uid=(
                TriState.nop()
                if isinstance(dto.container_uid, Sentinel)
                else TriState.from_graphql(dto.container_uid)
            ),
            container_main_gid=(
                TriState.nop()
                if isinstance(dto.container_main_gid, Sentinel)
                else TriState.from_graphql(dto.container_main_gid)
            ),
            container_gids=(
                TriState.nop()
                if isinstance(dto.container_gids, Sentinel)
                else TriState.from_graphql(dto.container_gids)
            ),
            group_ids=(
                OptionalState.nop()
                if isinstance(dto.group_ids, Sentinel) or dto.group_ids is None
                else OptionalState.update([str(gid) for gid in dto.group_ids])
            ),
        )

        items.append(UserUpdateSpec(user_id=user_item.user_id, updater_spec=updater_spec))

    action = BulkModifyUserAction(items=items)
    result = await ctx.processors.user.bulk_modify_users.wait_for_complete(action)

    updated_users = [UserV2GQL.from_data(user_data) for user_data in result.data.successes]
    failed = [
        BulkUpdateUserV2ErrorGQL(
            user_id=items[error.index].user_id,
            message=str(error.exception),
        )
        for error in result.data.failures
    ]

    return BulkUpdateUsersV2PayloadGQL(
        updated_users=updated_users,
        failed=failed,
    )


@strawberry.mutation(
    description=(
        "Added in 26.2.0. Update the current user's information. "
        "Users can only update their own profile. "
        "Some fields may be restricted based on user role."
    )
)  # type: ignore[misc]
async def update_user_v2(
    info: Info[StrawberryGQLContext],
    input: UpdateUserV2InputGQL,
) -> UpdateUserPayloadGQL:
    """Update the current user's own information.

    Args:
        info: Strawberry GraphQL context.
        input: User update input with fields to modify.

    Returns:
        UpdateUserPayloadGQL with the updated user.

    Raises:
        NotImplementedError: This mutation is not yet implemented.
    """
    raise NotImplementedError("update_user_v2 is not yet implemented")


# Delete UpdateUserV2InputGQLlete)


@strawberry.mutation(
    description=(
        "Added in 26.2.0. Soft-delete a user (admin only). "
        "Requires superadmin privileges. "
        "Sets the user status to DELETED but preserves data."
    )
)  # type: ignore[misc]
async def admin_delete_user_v2(
    info: Info[StrawberryGQLContext],
    user_id: UUID,
) -> DeleteUserPayloadGQL:
    """Soft-delete a single user.

    Args:
        info: Strawberry GraphQL context.
        user_id: UUID of the user to delete.

    Returns:
        DeleteUserPayloadGQL indicating success.

    Raises:
        NotImplementedError: This mutation is not yet implemented.
    """
    check_admin_only()
    raise NotImplementedError("admin_delete_user_v2 is not yet implemented")


@strawberry.mutation(
    description=(
        "Added in 26.2.0. Soft-delete multiple users (admin only). "
        "Requires superadmin privileges. "
        "Sets user status to DELETED but preserves data."
    )
)  # type: ignore[misc]
async def admin_delete_users_v2(
    info: Info[StrawberryGQLContext],
    input: DeleteUsersInputGQL,
) -> DeleteUsersPayloadGQL:
    """Soft-delete multiple users.

    Args:
        info: Strawberry GraphQL context.
        input: Input containing list of user UUIDs to delete.

    Returns:
        DeleteUsersPayloadGQL with count of deleted users.

    Raises:
        NotImplementedError: This mutation is not yet implemented.
    """
    check_admin_only()
    raise NotImplementedError("admin_delete_users_v2 is not yet implemented")


# Purge Mutations (Hard Delete)


@strawberry.mutation(
    description=(
        "Added in 26.2.0. Permanently delete a user and all associated data (admin only). "
        "Requires superadmin privileges. "
        "This action is IRREVERSIBLE. All user data, sessions, and resources will be deleted."
    )
)  # type: ignore[misc]
async def admin_purge_user_v2(
    info: Info[StrawberryGQLContext],
    input: PurgeUserInputGQL,
) -> PurgeUserPayloadGQL:
    """Permanently delete a single user.

    Args:
        info: Strawberry GraphQL context.
        input: Purge input with email and options.

    Returns:
        PurgeUserPayloadGQL indicating success.

    Raises:
        NotImplementedError: This mutation is not yet implemented.
    """
    check_admin_only()
    raise NotImplementedError("admin_purge_user_v2 is not yet implemented")


@strawberry.mutation(
    description=(
        "Added in 26.3.0. Permanently delete multiple users in bulk (admin only). "
        "Requires superadmin privileges. "
        "This action is IRREVERSIBLE. All user data will be deleted."
    )
)  # type: ignore[misc]
async def admin_bulk_purge_users_v2(
    info: Info[StrawberryGQLContext],
    input: BulkPurgeUsersV2InputGQL,
) -> BulkPurgeUsersV2PayloadGQL:
    """Permanently delete multiple users in bulk.

    Args:
        info: Strawberry GraphQL context.
        input: Bulk purge input with user IDs and options.

    Returns:
        BulkPurgeUsersV2PayloadGQL with purged count and failures.
    """
    check_admin_only()
    ctx = info.context

    me = current_user()
    if me is None:
        raise UnreachableError("User context is not available after check_admin_only()")

    options = input.options
    action = BulkPurgeUserAction(
        user_ids=input.user_ids,
        admin_user_id=me.user_id,
        purge_shared_vfolders=(
            OptionalState.update(options.purge_shared_vfolders)
            if options and options.purge_shared_vfolders
            else OptionalState.nop()
        ),
        delegate_endpoint_ownership=(
            OptionalState.update(options.delegate_endpoint_ownership)
            if options and options.delegate_endpoint_ownership
            else OptionalState.nop()
        ),
    )
    result = await ctx.processors.user.bulk_purge_users.wait_for_complete(action)

    failed = [
        BulkPurgeUserV2ErrorGQL(
            user_id=error.user_id,
            message=str(error.exception),
        )
        for error in result.data.failures
    ]

    return BulkPurgeUsersV2PayloadGQL(
        purged_count=result.data.purged_count(),
        failed=failed,
    )


# IP Allowlist Mutations


@strawberry.mutation(
    description=(
        "Added in 26.4.0. Update the current user's allowed client IP list. "
        "Set allowed_client_ip to null to remove all IP restrictions. "
        "When force is false, the operation fails if the current request IP "
        "would be excluded by the new allowlist (lockout prevention)."
    )
)  # type: ignore[misc]
async def update_my_allowed_client_ip(
    info: Info[StrawberryGQLContext],
    input: UpdateMyAllowedClientIPInputGQL,
) -> UpdateMyAllowedClientIPPayloadGQL:
    """Update the current user's allowed client IP addresses."""
    me = current_user()
    if me is None:
        raise UnreachableError("User context is not available")
    ctx = info.context

    # Get user email (needed for ModifyUserAction)
    user_result = await ctx.processors.user.get_user.wait_for_complete(
        GetUserAction(user_uuid=me.user_id)
    )
    email = user_result.user.email

    new_allowlist = input.allowed_client_ip

    if new_allowlist is not None:
        # Validate CIDR format for each entry
        for ip_str in new_allowlist:
            try:
                ReadableCIDR(ip_str)
            except (InvalidIpAddressValue, ValueError) as e:
                raise InvalidAPIParameters(f"Invalid IP address or CIDR: {ip_str}") from e

        # Lockout prevention when force=False
        if not input.force:
            if len(new_allowlist) == 0:
                raise InvalidAPIParameters(
                    "Empty allowlist would block all access. "
                    "Use force=true to override this safety check."
                )

            client_ip = current_client_ip()
            if client_ip is not None:
                try:
                    client_addr: ReadableCIDR[ipaddress.IPv4Network | ipaddress.IPv6Network] = (
                        ReadableCIDR(client_ip, is_network=False)
                    )
                except (InvalidIpAddressValue, ValueError) as e:
                    raise InvalidAPIParameters(
                        "Cannot verify current client IP for lockout prevention. "
                        "Use force=true to override this safety check."
                    ) from e
                allowed_networks: list[
                    ReadableCIDR[ipaddress.IPv4Network | ipaddress.IPv6Network]
                ] = [ReadableCIDR(ip_str) for ip_str in new_allowlist]
                if not any(
                    client_addr.address in network.address
                    for network in allowed_networks
                    if network.address is not None
                ):
                    raise InvalidAPIParameters(
                        f"Current IP ({client_ip}) is not in the new allowlist. "
                        "Use force=true to override this safety check."
                    )

        allowed_client_ip = TriState.update(new_allowlist)
    else:
        allowed_client_ip = TriState.nullify()

    updater_spec = UserUpdaterSpec(allowed_client_ip=allowed_client_ip)
    action = ModifyUserAction(
        email=email,
        updater=Updater(spec=updater_spec, pk_value=email),
    )
    await ctx.processors.user.modify_user.wait_for_complete(action)

    return UpdateMyAllowedClientIPPayloadGQL(success=True)
