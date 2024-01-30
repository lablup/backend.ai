from typing import Any, Dict, Sequence

from ...cli.types import Undefined, undefined
from ..output.fields import keypair_fields
from ..output.types import FieldSpec, PaginatedResult
from ..pagination import fetch_paginated_result
from ..session import api_session
from ..types import set_if_set
from .base import BaseFunction, api_function

__all__ = ("KeyPair",)

_default_list_fields = (
    keypair_fields["user_id"],
    keypair_fields["access_key"],
    keypair_fields["secret_key"],
    keypair_fields["is_active"],
    keypair_fields["is_admin"],
    keypair_fields["created_at"],
)

_default_detail_fields = (
    keypair_fields["user_id"],
    keypair_fields["access_key"],
    keypair_fields["secret_key"],
    keypair_fields["is_active"],
    keypair_fields["is_admin"],
)

_default_result_fields = (
    keypair_fields["access_key"],
    keypair_fields["secret_key"],
)


class KeyPair(BaseFunction):
    """
    Provides interactions with keypairs.
    """

    def __init__(self, access_key: str):
        self.access_key = access_key

    @api_function
    @classmethod
    async def create(
        cls,
        user_id: int | str,
        is_active: bool = True,
        is_admin: bool = False,
        resource_policy: str | Undefined = undefined,
        rate_limit: int | Undefined = undefined,
        fields: Sequence[FieldSpec] = _default_result_fields,
    ) -> dict:
        """
        Creates a new keypair with the given options.
        You need an admin privilege for this operation.
        """
        uid_type = "Int!" if isinstance(user_id, int) else "String!"
        q = (
            "mutation($user_id: {0}, $input: KeyPairInput!) {{".format(uid_type)
            + "  create_keypair(user_id: $user_id, props: $input) {"
            "    ok msg keypair { $fields }"
            "  }"
            "}"
        )
        q = q.replace("$fields", " ".join(f.field_ref for f in fields))
        inputs = {
            "is_active": is_active,
            "is_admin": is_admin,
        }
        set_if_set(inputs, "resource_policy", resource_policy)
        set_if_set(inputs, "rate_limit", rate_limit)
        variables = {
            "user_id": user_id,
            "input": inputs,
        }
        data = await api_session.get().Admin._query(q, variables)
        return data["create_keypair"]

    @api_function
    @classmethod
    async def update(
        cls,
        access_key: str,
        is_active: bool | Undefined = undefined,
        is_admin: bool | Undefined = undefined,
        resource_policy: str | Undefined = undefined,
        rate_limit: int | Undefined = undefined,
    ) -> dict:
        """
        Creates a new keypair with the given options.
        You need an admin privilege for this operation.
        """
        q = (
            "mutation($access_key: String!, $input: ModifyKeyPairInput!) {"
            + "  modify_keypair(access_key: $access_key, props: $input) {    ok msg  }}"
        )
        inputs: dict[str, Any] = {}
        set_if_set(inputs, "is_active", is_active)
        set_if_set(inputs, "is_admin", is_admin)
        set_if_set(inputs, "resource_policy", resource_policy)
        set_if_set(inputs, "rate_limit", rate_limit)
        variables = {
            "access_key": access_key,
            "input": inputs,
        }
        data = await api_session.get().Admin._query(q, variables)
        return data["modify_keypair"]

    @api_function
    @classmethod
    async def delete(cls, access_key: str):
        """
        Deletes an existing keypair with given ACCESSKEY.
        """
        q = (
            "mutation($access_key: String!) {"
            "  delete_keypair(access_key: $access_key) {"
            "    ok msg"
            "  }"
            "}"
        )
        variables = {
            "access_key": access_key,
        }
        data = await api_session.get().Admin._query(q, variables)
        return data["delete_keypair"]

    @api_function
    @classmethod
    async def list(
        cls,
        user_id: int | str | None = None,
        is_active: bool | None = None,
        fields: Sequence[FieldSpec] = _default_list_fields,
    ) -> Sequence[dict]:
        """
        Lists the keypairs.
        You need an admin privilege for this operation.
        """
        if user_id is None:
            q = "query($is_active: Boolean) {  keypairs(is_active: $is_active) {    $fields  }}"
        else:
            uid_type = "Int!" if isinstance(user_id, int) else "String!"
            q = (
                "query($email: {0}, $is_active: Boolean) {{".format(uid_type)
                + "  keypairs(email: $email, is_active: $is_active) {    $fields  }}"
            )
        q = q.replace("$fields", " ".join(f.field_ref for f in fields))
        variables: Dict[str, Any] = {
            "is_active": is_active,
        }
        if user_id is not None:
            variables["email"] = user_id
        data = await api_session.get().Admin._query(q, variables)
        return data["keypairs"]

    @api_function
    @classmethod
    async def paginated_list(
        cls,
        is_active: bool | None = None,
        domain_name: str | None = None,
        *,
        user_id: str | None = None,
        fields: Sequence[FieldSpec] = _default_list_fields,
        page_offset: int = 0,
        page_size: int = 20,
        filter: str | None = None,
        order: str | None = None,
    ) -> PaginatedResult[dict]:
        """
        Lists the keypairs.
        You need an admin privilege for this operation.
        """
        variables = {
            "is_active": (is_active, "Boolean"),
            "domain_name": (domain_name, "String"),
            "filter": (filter, "String"),
            "order": (order, "String"),
        }
        if user_id is not None:
            variables["email"] = (user_id, "String")
        return await fetch_paginated_result(
            "keypair_list",
            variables,
            fields,
            page_offset=page_offset,
            page_size=page_size,
        )

    @api_function
    async def info(self, fields: Sequence[FieldSpec] = _default_detail_fields) -> dict:
        """
        Returns the keypair's information such as resource limits.

        :param fields: Additional per-agent query fields to fetch.

        .. versionadded:: 18.12
        """
        q = "query {  keypair {    $fields  }}"
        q = q.replace("$fields", " ".join(f.field_ref for f in fields))
        data = await api_session.get().Admin._query(q)
        return data["keypair"]

    @api_function
    @classmethod
    async def activate(cls, access_key: str) -> dict:
        """
        Activates this keypair.
        You need an admin privilege for this operation.
        """
        q = (
            "mutation($access_key: String!, $input: ModifyKeyPairInput!) {"
            + "  modify_keypair(access_key: $access_key, props: $input) {    ok msg  }}"
        )
        variables = {
            "access_key": access_key,
            "input": {
                "is_active": True,
                "is_admin": None,
                "resource_policy": None,
                "rate_limit": None,
            },
        }
        data = await api_session.get().Admin._query(q, variables)
        return data["modify_keypair"]

    @api_function
    @classmethod
    async def deactivate(cls, access_key: str) -> dict:
        """
        Deactivates this keypair.
        Deactivated keypairs cannot make any API requests
        unless activated again by an administrator.
        You need an admin privilege for this operation.
        """
        q = (
            "mutation($access_key: String!, $input: ModifyKeyPairInput!) {"
            + "  modify_keypair(access_key: $access_key, props: $input) {    ok msg  }}"
        )
        variables = {
            "access_key": access_key,
            "input": {
                "is_active": False,
                "is_admin": None,
                "resource_policy": None,
                "rate_limit": None,
            },
        }
        data = await api_session.get().Admin._query(q, variables)
        return data["modify_keypair"]
