from typing import Any, Iterable, Sequence

from ...cli.types import Undefined, undefined
from ..output.fields import keypair_resource_policy_fields
from ..output.types import FieldSpec
from ..session import api_session
from ..types import set_if_set
from .base import BaseFunction, api_function, resolve_fields

__all__ = ("KeypairResourcePolicy",)

_default_list_fields = (
    keypair_resource_policy_fields["name"],
    keypair_resource_policy_fields["created_at"],
    keypair_resource_policy_fields["total_resource_slots"],
    keypair_resource_policy_fields["max_concurrent_sessions"],
    keypair_resource_policy_fields["idle_timeout"],
    keypair_resource_policy_fields["max_containers_per_session"],
    keypair_resource_policy_fields["allowed_vfolder_hosts"],
    keypair_resource_policy_fields["max_session_lifetime"],
    keypair_resource_policy_fields["max_pending_session_count"],
    keypair_resource_policy_fields["max_pending_session_resource_slots"],
    keypair_resource_policy_fields["max_concurrent_sftp_sessions"],
)

_default_detail_fields = (
    keypair_resource_policy_fields["name"],
    keypair_resource_policy_fields["created_at"],
    keypair_resource_policy_fields["total_resource_slots"],
    keypair_resource_policy_fields["max_concurrent_sessions"],
    keypair_resource_policy_fields["idle_timeout"],
    keypair_resource_policy_fields["max_containers_per_session"],
    keypair_resource_policy_fields["allowed_vfolder_hosts"],
    keypair_resource_policy_fields["max_session_lifetime"],
    keypair_resource_policy_fields["max_pending_session_count"],
    keypair_resource_policy_fields["max_pending_session_resource_slots"],
    keypair_resource_policy_fields["max_concurrent_sftp_sessions"],
)


class KeypairResourcePolicy(BaseFunction):
    """
    Provides interactions with keypair resource policy.
    """

    def __init__(self, access_key: str):
        self.access_key = access_key

    @api_function
    @classmethod
    async def create(
        cls,
        name: str,
        *,
        default_for_unspecified: str,
        total_resource_slots: str,
        max_session_lifetime: int,
        max_concurrent_sessions: int,
        max_concurrent_sftp_sessions: int,
        max_containers_per_session: int,
        idle_timeout: int,
        vfolder_host_perms: str | Undefined = undefined,
        max_pending_session_count: int | Undefined = undefined,
        max_pending_session_resource_slots: str | Undefined = undefined,
        fields: Iterable[FieldSpec | str] | None = None,
    ) -> dict:
        """
        Creates a new keypair resource policy with the given options.
        You need an admin privilege for this operation.
        """
        q = (
            "mutation($name: String!, $input: CreateKeyPairResourcePolicyInput!) {"
            + "  create_keypair_resource_policy(name: $name, props: $input) {"
            "    ok msg resource_policy { $fields }"
            "  }"
            "}"
        )
        resolved_fields = resolve_fields(
            fields, keypair_resource_policy_fields, (keypair_resource_policy_fields["name"],)
        )
        q = q.replace("$fields", " ".join(resolved_fields))
        inputs = {
            "default_for_unspecified": default_for_unspecified,
            "total_resource_slots": total_resource_slots,
            "max_session_lifetime": max_session_lifetime,
            "max_concurrent_sessions": max_concurrent_sessions,
            "max_concurrent_sftp_sessions": max_concurrent_sftp_sessions,
            "max_containers_per_session": max_containers_per_session,
            "idle_timeout": idle_timeout,
            "allowed_vfolder_hosts": vfolder_host_perms,
            "max_pending_session_count": max_pending_session_count,
            "max_pending_session_resource_slots": max_pending_session_resource_slots,
        }
        set_if_set(inputs, "allowed_vfolder_hosts", vfolder_host_perms)
        variables = {
            "name": name,
            "input": inputs,
        }
        data = await api_session.get().Admin._query(q, variables)
        return data["create_keypair_resource_policy"]

    @api_function
    @classmethod
    async def update(
        cls,
        name: str,
        *,
        default_for_unspecified: int | Undefined = undefined,
        max_session_lifetime: int | Undefined = undefined,
        max_concurrent_sessions: int | Undefined = undefined,
        max_concurrent_sftp_sessions: int | Undefined = undefined,
        max_containers_per_session: int | Undefined = undefined,
        idle_timeout: int | Undefined = undefined,
        total_resource_slots: str | Undefined = undefined,
        vfolder_host_perms: str | Undefined = undefined,
        max_pending_session_count: int | Undefined = undefined,
        max_pending_session_resource_slots: str | Undefined = undefined,
    ) -> dict:
        """
        Updates an existing keypair resource policy with the given options.
        You need an admin privilege for this operation.
        """
        q = (
            "mutation($name: String!, $input: ModifyKeyPairResourcePolicyInput!) {"
            + "  modify_keypair_resource_policy(name: $name, props: $input) {    ok msg  }}"
        )
        inputs: dict[str, Any] = {}
        set_if_set(inputs, "default_for_unspecified", default_for_unspecified)
        set_if_set(inputs, "total_resource_slots", total_resource_slots)
        set_if_set(inputs, "max_session_lifetime", max_session_lifetime)
        set_if_set(inputs, "max_concurrent_sessions", max_concurrent_sessions)
        set_if_set(inputs, "max_concurrent_sftp_sessions", max_concurrent_sftp_sessions)
        set_if_set(inputs, "max_containers_per_session", max_containers_per_session)
        set_if_set(inputs, "idle_timeout", idle_timeout)
        set_if_set(inputs, "allowed_vfolder_hosts", vfolder_host_perms)
        set_if_set(inputs, "max_pending_session_count", max_pending_session_count)
        set_if_set(inputs, "max_pending_session_resource_slots", max_pending_session_resource_slots)
        variables = {
            "name": name,
            "input": inputs,
        }
        data = await api_session.get().Admin._query(q, variables)
        return data["modify_keypair_resource_policy"]

    @api_function
    @classmethod
    async def delete(cls, name: str) -> dict:
        """
        Deletes an existing keypair resource policy with given name.
        You need an admin privilege for this operation.
        """
        q = (
            "mutation($name: String!) {"
            + "  delete_keypair_resource_policy(name: $name) {    ok msg  }}"
        )
        variables = {
            "name": name,
        }
        data = await api_session.get().Admin._query(q, variables)
        return data["delete_keypair_resource_policy"]

    @api_function
    @classmethod
    async def list(
        cls,
        fields: Sequence[FieldSpec] = _default_list_fields,
    ) -> Sequence[dict]:
        """
        Lists the keypair resource policies.
        You need an admin privilege for this operation.
        """
        q = "query {  keypair_resource_policies {    $fields  }}"
        q = q.replace("$fields", " ".join(f.field_ref for f in fields))
        data = await api_session.get().Admin._query(q)
        return data["keypair_resource_policies"]

    @api_function
    async def info(
        self,
        name: str,
        fields: Sequence[FieldSpec] = _default_detail_fields,
    ) -> dict:
        """
        Returns the resource policy's information.

        :param fields: Additional per-agent query fields to fetch.

        .. versionadded:: 19.03
        """
        q = "query($name: String) {  keypair_resource_policy(name: $name) {    $fields  }}"
        q = q.replace("$fields", " ".join(f.field_ref for f in fields))
        variables = {
            "name": name,
        }
        data = await api_session.get().Admin._query(q, variables)
        return data["keypair_resource_policy"]
