from __future__ import annotations

import enum
import textwrap
import uuid
from typing import Any, Iterable, Mapping, Sequence, Union

from ...cli.types import Undefined, undefined
from ..auth import AuthToken, AuthTokenTypes
from ..output.fields import user_fields
from ..output.types import FieldSpec, PaginatedResult
from ..pagination import fetch_paginated_result
from ..request import Request
from ..session import api_session
from ..types import set_if_set
from .base import BaseFunction, api_function, resolve_fields

__all__ = (
    "User",
    "UserStatus",
    "UserRole",
)


_default_list_fields = (
    user_fields["uuid"],
    user_fields["role"],
    user_fields["username"],
    user_fields["email"],
    user_fields["need_password_change"],
    user_fields["status"],
    user_fields["status_info"],
    user_fields["is_active"],
    user_fields["created_at"],
    user_fields["domain_name"],
    user_fields["groups"],
    user_fields["allowed_client_ip"],
    user_fields["totp_activated"],
    user_fields["sudo_session_enabled"],
    user_fields["main_access_key"],
)

_default_detail_fields = (
    user_fields["uuid"],
    user_fields["username"],
    user_fields["email"],
    user_fields["need_password_change"],
    user_fields["status"],
    user_fields["status_info"],
    user_fields["created_at"],
    user_fields["domain_name"],
    user_fields["role"],
    user_fields["groups"],
    user_fields["allowed_client_ip"],
    user_fields["totp_activated"],
    user_fields["sudo_session_enabled"],
    user_fields["main_access_key"],
)


class UserRole(enum.StrEnum):
    """
    The role (privilege level) of users.
    """

    SUPERADMIN = "superadmin"
    ADMIN = "admin"
    USER = "user"
    MONITOR = "monitor"


class UserStatus(enum.StrEnum):
    """
    The detailed status of users to represent the signup process and account lifecycles.
    """

    ACTIVE = "active"
    INACTIVE = "inactive"
    DELETED = "deleted"
    BEFORE_VERIFICATION = "before-verification"


class User(BaseFunction):
    """
    Provides interactions with users.
    """

    @api_function
    @classmethod
    async def authorize(
        cls,
        username: str,
        password: str,
        *,
        extra_args: Mapping[str, Any] = {},
        token_type: AuthTokenTypes = AuthTokenTypes.KEYPAIR,
    ) -> AuthToken:
        """
        Authorize the given credentials and get the API authentication token.
        This function can be invoked anonymously; i.e., it does not require
        access/secret keys in the session config as its purpose is to "get" them.

        Its functionality will be expanded in the future to support multiple types
        of authentication methods.
        """
        rqst = Request("POST", "/auth/authorize")
        body = {
            "type": token_type.value,
            "domain": api_session.get().config.domain,
            "username": username,
            "password": password,
        }
        for k, v in extra_args.items():
            body[k] = v
        rqst.set_json(body)
        async with rqst.fetch() as resp:
            data = await resp.json()
            return AuthToken(
                type=token_type,
                content=data["data"],
            )

    @api_function
    @classmethod
    async def list(
        cls,
        status: str | None = None,
        group: str | None = None,
        fields: Sequence[FieldSpec] = _default_list_fields,
    ) -> Sequence[dict]:
        """
        Fetches the list of users. Domain admins can only get domain users.

        :param status: Fetches users in a specific status
                       (active, inactive, deleted, before-verification).
        :param group: Fetch users in a specific group.
        :param fields: Additional per-user query fields to fetch.
        """
        query = textwrap.dedent(
            """\
            query($status: String, $group: UUID) {
                users(status: $status, group_id: $group) {$fields}
            }
        """
        )
        query = query.replace("$fields", " ".join(f.field_ref for f in fields))
        variables = {
            "status": status,
            "group": group,
        }
        data = await api_session.get().Admin._query(query, variables)
        return data["users"]

    @api_function
    @classmethod
    async def paginated_list(
        cls,
        status: str | None = None,
        group: str | None = None,
        *,
        fields: Sequence[FieldSpec] = _default_list_fields,
        page_offset: int = 0,
        page_size: int = 20,
        filter: str | None = None,
        order: str | None = None,
    ) -> PaginatedResult[dict]:
        """
        Fetches the list of users. Domain admins can only get domain users.

        :param status: Fetches users in a specific status
                       (active, inactive, deleted, before-verification).
        :param group: Fetch users in a specific group.
        :param fields: Additional per-user query fields to fetch.
        """
        return await fetch_paginated_result(
            "user_list",
            {
                "status": (status, "String"),
                "group_id": (group, "UUID"),
                "filter": (filter, "String"),
                "order": (order, "String"),
            },
            fields,
            page_offset=page_offset,
            page_size=page_size,
        )

    @api_function
    @classmethod
    async def detail(
        cls,
        email: str | None = None,
        fields: Sequence[FieldSpec] = _default_detail_fields,
    ) -> Sequence[dict]:
        """
        Fetch information of a user. If email is not specified,
        requester's information will be returned.

        :param email: Email of the user to fetch.
        :param fields: Additional per-user query fields to fetch.
        """
        if email is None:
            query = textwrap.dedent(
                """\
                query {
                    user {$fields}
                }
            """
            )
        else:
            query = textwrap.dedent(
                """\
                query($email: String) {
                    user(email: $email) {$fields}
                }
            """
            )
        query = query.replace("$fields", " ".join(f.field_ref for f in fields))
        variables = {"email": email}
        data = await api_session.get().Admin._query(query, variables if email is not None else None)
        return data["user"]

    @api_function
    @classmethod
    async def detail_by_uuid(
        cls,
        user_uuid: Union[str, uuid.UUID] | None = None,
        fields: Sequence[FieldSpec] = _default_detail_fields,
    ) -> Sequence[dict]:
        """
        Fetch information of a user by user's uuid. If user_uuid is not specified,
        requester's information will be returned.

        :param user_uuid: UUID of the user to fetch.
        :param fields: Additional per-user query fields to fetch.
        """
        if user_uuid is None:
            query = textwrap.dedent(
                """\
                query {
                    user {$fields}
                }
            """
            )
        else:
            query = textwrap.dedent(
                """\
                query($user_id: ID) {
                    user_from_uuid(user_id: $user_id) {$fields}
                }
            """
            )
        query = query.replace("$fields", " ".join(f.field_ref for f in fields))
        variables = {"user_id": str(user_uuid)}
        data = await api_session.get().Admin._query(
            query, variables if user_uuid is not None else None
        )
        return data["user_from_uuid"]

    @api_function
    @classmethod
    async def create(
        cls,
        domain_name: str,
        email: str,
        password: str,
        *,
        username: str | Undefined = undefined,
        full_name: str | Undefined = undefined,
        role: UserRole | str = UserRole.USER,
        status: UserStatus | str = UserStatus.ACTIVE,
        need_password_change: bool = False,
        description: str = "",
        allowed_client_ip: Iterable[str] | Undefined = undefined,
        totp_activated: bool = False,
        group_ids: Iterable[str] | Undefined = undefined,
        sudo_session_enabled: bool = False,
        fields: Iterable[FieldSpec | str] | None = None,
    ) -> dict:
        """
        Creates a new user with the given options.
        You need an admin privilege for this operation.
        """
        query = textwrap.dedent(
            """\
            mutation($email: String!, $input: UserInput!) {
                create_user(email: $email, props: $input) {
                    ok msg user {$fields}
                }
            }
        """
        )
        default_fields = (
            user_fields["domain_name"],
            user_fields["email"],
            user_fields["username"],
            user_fields["uuid"],
        )
        resolved_fields = resolve_fields(fields, user_fields, default_fields)
        query = query.replace("$fields", " ".join(resolved_fields))
        inputs = {
            "password": password,
            "role": role.value if isinstance(role, UserRole) else role,
            "status": status.value if isinstance(status, UserStatus) else status,
            "need_password_change": need_password_change,
            "description": description,
            "domain_name": domain_name,
            "totp_activated": totp_activated,
            "sudo_session_enabled": sudo_session_enabled,
        }
        set_if_set(inputs, "username", username)
        set_if_set(inputs, "full_name", full_name)
        set_if_set(inputs, "allowed_client_ip", allowed_client_ip)
        set_if_set(inputs, "group_ids", group_ids)
        variables = {
            "email": email,
            "input": inputs,
        }
        data = await api_session.get().Admin._query(query, variables)
        return data["create_user"]

    @api_function
    @classmethod
    async def update(
        cls,
        email: str,
        *,
        password: str | Undefined = undefined,
        username: str | Undefined = undefined,
        full_name: str | Undefined = undefined,
        domain_name: str | Undefined = undefined,
        role: UserRole | str | Undefined = undefined,
        status: UserStatus | str | Undefined = undefined,
        need_password_change: bool | Undefined = undefined,
        description: str | Undefined = undefined,
        allowed_client_ip: Iterable[str] | Undefined = undefined,
        totp_activated: bool | Undefined = undefined,
        group_ids: Iterable[str] | Undefined = undefined,
        sudo_session_enabled: bool | Undefined = undefined,
        main_access_key: str | Undefined = undefined,
        fields: Iterable[FieldSpec | str] | None = None,
    ) -> dict:
        """
        Update existing user.
        You need an admin privilege for this operation.
        """
        query = textwrap.dedent(
            """\
            mutation($email: String!, $input: ModifyUserInput!) {
                modify_user(email: $email, props: $input) {
                    ok msg
                }
            }
        """
        )
        inputs: dict[str, Any] = {}
        set_if_set(inputs, "password", password)
        set_if_set(inputs, "username", username)
        set_if_set(inputs, "full_name", full_name)
        set_if_set(inputs, "domain_name", domain_name)
        set_if_set(inputs, "role", role.value if isinstance(role, UserRole) else role)
        set_if_set(inputs, "status", status.value if isinstance(status, UserStatus) else status)
        set_if_set(inputs, "need_password_change", need_password_change)
        set_if_set(inputs, "description", description)
        set_if_set(inputs, "allowed_client_ip", allowed_client_ip)
        set_if_set(inputs, "totp_activated", totp_activated)
        set_if_set(inputs, "group_ids", group_ids)
        set_if_set(inputs, "sudo_session_enabled", sudo_session_enabled)
        set_if_set(inputs, "main_access_key", main_access_key)
        variables = {
            "email": email,
            "input": inputs,
        }
        data = await api_session.get().Admin._query(query, variables)
        return data["modify_user"]

    @api_function
    @classmethod
    async def delete(cls, email: str):
        """
        Inactivates an existing user.
        """
        query = textwrap.dedent(
            """\
            mutation($email: String!) {
                delete_user(email: $email) {
                    ok msg
                }
            }
        """
        )
        variables = {"email": email}
        data = await api_session.get().Admin._query(query, variables)
        return data["delete_user"]

    @api_function
    @classmethod
    async def purge(cls, email: str, purge_shared_vfolders=False):
        """
        Deletes an existing user.

        User's virtual folders are also deleted, except the ones shared with other users.
        Shared virtual folder's ownership will be transferred to the requested admin.
        To delete shared folders as well, set ``purge_shared_vfolders`` to ``True``.
        """
        query = textwrap.dedent(
            """\
            mutation($email: String!, $input: PurgeUserInput!) {
                purge_user(email: $email, props: $input) {
                    ok msg
                }
            }
        """
        )
        variables = {
            "email": email,
            "input": {
                "purge_shared_vfolders": purge_shared_vfolders,
            },
        }
        data = await api_session.get().Admin._query(query, variables)
        return data["purge_user"]
