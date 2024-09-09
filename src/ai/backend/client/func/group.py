import textwrap
from typing import Any, Iterable, Optional, Sequence

from ai.backend.client.output.fields import group_fields
from ai.backend.client.output.types import FieldSpec

from ...cli.types import Undefined, undefined
from ..session import api_session
from ..types import set_if_set
from .base import BaseFunction, api_function, resolve_fields

__all__ = ("Group",)

_default_list_fields = (
    group_fields["id"],
    group_fields["name"],
    group_fields["is_active"],
    group_fields["created_at"],
    group_fields["integration_id"],
)
_default_detail_fields = (
    group_fields["id"],
    group_fields["name"],
    group_fields["description"],
    group_fields["is_active"],
    group_fields["created_at"],
    group_fields["domain_name"],
    group_fields["total_resource_slots"],
    group_fields["allowed_vfolder_hosts"],
    group_fields["integration_id"],
)


class Group(BaseFunction):
    """
    Provides a shortcut of :func:`Group.query()
    <ai.backend.client.admin.Admin.query>` that fetches various group information.

    .. note::

      All methods in this function class require your API access key to
      have the *admin* privilege.
    """

    @api_function
    @classmethod
    async def from_name(
        cls,
        name: str,
        *,
        fields: Iterable[FieldSpec | str] = None,
        domain_name: str = None,
    ) -> Sequence[dict]:
        """
        Find the group(s) by its name.
        It may return multiple groups when there are groups with the same name
        in different domains and it is invoked with a super-admin account
        without setting the domain name.

        :param domain_name: Name of domain to get groups from.
        :param fields: Per-group query fields to fetch.
        """
        query = textwrap.dedent(
            """\
            query($name: String!, $domain_name: String) {
                groups_by_name(name: $name, domain_name: $domain_name) {$fields}
            }
        """
        )
        resolved_fields = resolve_fields(fields, group_fields, _default_detail_fields)
        query = query.replace("$fields", " ".join(resolved_fields))
        variables = {
            "name": name,
            "domain_name": domain_name,
        }
        data = await api_session.get().Admin._query(query, variables)
        return data["groups_by_name"]

    @api_function
    @classmethod
    async def list(
        cls,
        domain_name: str,
        fields: Sequence[FieldSpec] = _default_list_fields,
    ) -> Sequence[dict]:
        """
        Fetches the list of groups.

        :param domain_name: Name of domain to list groups.
        :param fields: Per-group query fields to fetch.
        """
        if fields is None:
            fields = _default_list_fields
        query = textwrap.dedent(
            """\
            query($domain_name: String) {
                groups(domain_name: $domain_name) {$fields}
            }
        """
        )
        query = query.replace("$fields", " ".join(f.field_ref for f in fields))
        variables = {"domain_name": domain_name}
        data = await api_session.get().Admin._query(query, variables)
        return data["groups"]

    @api_function
    @classmethod
    async def detail(
        cls,
        gid: str,
        fields: Sequence[FieldSpec] = _default_detail_fields,
    ) -> dict:
        """
        Fetch information of a group with group ID.

        :param gid: ID of the group to fetch.
        :param fields: Additional per-group query fields to fetch.
        """
        if fields is None:
            fields = _default_detail_fields
        query = textwrap.dedent(
            """\
            query($gid: UUID!) {
                group(id: $gid) {$fields}
            }
        """
        )
        query = query.replace("$fields", " ".join(f.field_ref for f in fields))
        variables = {"gid": gid}
        data = await api_session.get().Admin._query(query, variables)
        return data["group"]

    @api_function
    @classmethod
    async def create(
        cls,
        domain_name: str,
        name: str,
        *,
        description: str = "",
        is_active: bool = True,
        total_resource_slots: Optional[str] = None,
        allowed_vfolder_hosts: Optional[str] = None,
        integration_id: Optional[str] = None,
        fields: Iterable[FieldSpec | str] | None = None,
    ) -> dict:
        """
        Creates a new group with the given options.
        You need an admin privilege for this operation.
        """
        query = textwrap.dedent(
            """\
            mutation($name: String!, $input: GroupInput!) {
                create_group(name: $name, props: $input) {
                    ok msg group {$fields}
                }
            }
        """
        )
        resolved_fields = resolve_fields(
            fields,
            group_fields,
            (group_fields["id"], group_fields["domain_name"], group_fields["name"]),
        )
        query = query.replace("$fields", " ".join(resolved_fields))
        variables = {
            "name": name,
            "input": {
                "description": description,
                "is_active": is_active,
                "domain_name": domain_name,
                "total_resource_slots": total_resource_slots,
                "allowed_vfolder_hosts": allowed_vfolder_hosts,
                "integration_id": integration_id,
            },
        }
        data = await api_session.get().Admin._query(query, variables)
        return data["create_group"]

    @api_function
    @classmethod
    async def update(
        cls,
        gid: str,
        *,
        name: str | Undefined = undefined,
        description: str | Undefined = undefined,
        is_active: bool | Undefined = undefined,
        total_resource_slots: Optional[str] | Undefined = undefined,
        allowed_vfolder_hosts: Optional[str] | Undefined = undefined,
        integration_id: str | Undefined = undefined,
        fields: Iterable[FieldSpec | str] | None = None,
    ) -> dict:
        """
        Update existing group.
        You need an admin privilege for this operation.
        """
        query = textwrap.dedent(
            """\
            mutation($gid: UUID!, $input: ModifyGroupInput!) {
                modify_group(gid: $gid, props: $input) {
                    ok msg
                }
            }
        """
        )
        inputs: dict[str, Any] = {}
        set_if_set(inputs, "name", name)
        set_if_set(inputs, "description", description)
        set_if_set(inputs, "is_active", is_active)
        set_if_set(inputs, "total_resource_slots", total_resource_slots)
        set_if_set(inputs, "allowed_vfolder_hosts", allowed_vfolder_hosts)
        set_if_set(inputs, "integration_id", integration_id)
        variables = {
            "gid": gid,
            "input": inputs,
        }
        data = await api_session.get().Admin._query(query, variables)
        return data["modify_group"]

    @api_function
    @classmethod
    async def delete(cls, gid: str):
        """
        Inactivates the existing group. Does not actually delete it for safety.
        """
        query = textwrap.dedent(
            """\
            mutation($gid: UUID!) {
                delete_group(gid: $gid) {
                    ok msg
                }
            }
        """
        )
        variables = {"gid": gid}
        data = await api_session.get().Admin._query(query, variables)
        return data["delete_group"]

    @api_function
    @classmethod
    async def purge(cls, gid: str):
        """
        Delete the existing group. This action cannot be undone.
        """
        query = textwrap.dedent(
            """\
            mutation($gid: UUID!) {
                purge_group(gid: $gid) {
                    ok msg
                }
            }
        """
        )
        variables = {"gid": gid}
        data = await api_session.get().Admin._query(query, variables)
        return data["purge_group"]

    @api_function
    @classmethod
    async def add_users(
        cls, gid: str, user_uuids: Iterable[str], fields: Iterable[FieldSpec | str] = None
    ) -> dict:
        """
        Add users to a group.
        You need an admin privilege for this operation.
        """
        query = textwrap.dedent(
            """\
            mutation($gid: UUID!, $input: ModifyGroupInput!) {
                modify_group(gid: $gid, props: $input) {
                    ok msg
                }
            }
        """
        )
        variables = {
            "gid": gid,
            "input": {
                "user_update_mode": "add",
                "user_uuids": user_uuids,
            },
        }
        data = await api_session.get().Admin._query(query, variables)
        return data["modify_group"]

    @api_function
    @classmethod
    async def remove_users(
        cls, gid: str, user_uuids: Iterable[str], fields: Iterable[FieldSpec | str] = None
    ) -> dict:
        """
        Remove users from a group.
        You need an admin privilege for this operation.
        """
        query = textwrap.dedent(
            """\
            mutation($gid: UUID!, $input: ModifyGroupInput!) {
                modify_group(gid: $gid, props: $input) {
                    ok msg
                }
            }
        """
        )
        variables = {
            "gid": gid,
            "input": {
                "user_update_mode": "remove",
                "user_uuids": user_uuids,
            },
        }
        data = await api_session.get().Admin._query(query, variables)
        return data["modify_group"]
