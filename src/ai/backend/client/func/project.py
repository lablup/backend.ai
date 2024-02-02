import textwrap
from typing import Any, Iterable, Optional, Sequence

from ai.backend.client.output.fields import project_fields
from ai.backend.client.output.types import FieldSpec

from ...cli.types import Undefined, undefined
from ..session import api_session
from ..types import set_if_set
from .base import BaseFunction, api_function, resolve_fields

__all__ = ("Project",)

_default_list_fields = (
    project_fields["id"],
    project_fields["name"],
    project_fields["is_active"],
    project_fields["created_at"],
    project_fields["integration_id"],
)
_default_detail_fields = (
    project_fields["id"],
    project_fields["name"],
    project_fields["description"],
    project_fields["is_active"],
    project_fields["created_at"],
    project_fields["domain_name"],
    project_fields["total_resource_slots"],
    project_fields["allowed_vfolder_hosts"],
    project_fields["integration_id"],
)


class Project(BaseFunction):
    """
    Provides a shortcut of :func:`Project.query()
    <ai.backend.client.admin.Admin.query>` that fetches various project information.

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
        Find the project(s) by its name.
        It may return multiple projects when there are projects with the same name
        in different domains and it is invoked with a super-admin account
        without setting the domain name.

        :param domain_name: Name of domain to get projects from.
        :param fields: Per-project query fields to fetch.
        """
        query = textwrap.dedent(
            """\
            query($name: String!, $domain_name: String) {
                projects_by_name(name: $name, domain_name: $domain_name) {$fields}
            }
        """
        )
        resolved_fields = resolve_fields(fields, project_fields, _default_detail_fields)
        query = query.replace("$fields", " ".join(resolved_fields))
        variables = {
            "name": name,
            "domain_name": domain_name,
        }
        data = await api_session.get().Admin._query(query, variables)
        return data["projects_by_name"]

    @api_function
    @classmethod
    async def list(
        cls,
        domain_name: str,
        fields: Sequence[FieldSpec] = _default_list_fields,
    ) -> Sequence[dict]:
        """
        Fetches the list of projects.

        :param domain_name: Name of domain to list projects.
        :param fields: Per-project query fields to fetch.
        """
        if fields is None:
            fields = _default_list_fields
        query = textwrap.dedent(
            """\
            query($domain_name: String) {
                projects(domain_name: $domain_name) {$fields}
            }
        """
        )
        query = query.replace("$fields", " ".join(f.field_ref for f in fields))
        variables = {"domain_name": domain_name}
        data = await api_session.get().Admin._query(query, variables)
        return data["projects"]

    @api_function
    @classmethod
    async def detail(
        cls,
        pid: str,
        fields: Sequence[FieldSpec] = _default_detail_fields,
    ) -> dict:
        """
        Fetch information of a project with project ID.

        :param pid: ID of the project to fetch.
        :param fields: Additional per-project query fields to fetch.
        """
        if fields is None:
            fields = _default_detail_fields
        query = textwrap.dedent(
            """\
            query($pid: UUID!) {
                project(id: $pid) {$fields}
            }
        """
        )
        query = query.replace("$fields", " ".join(f.field_ref for f in fields))
        variables = {"pid": pid}
        data = await api_session.get().Admin._query(query, variables)
        return data["project"]

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
        Creates a new project with the given options.
        You need an admin privilege for this operation.
        """
        query = textwrap.dedent(
            """\
            mutation($name: String!, $input: ProjectInput!) {
                create_project(name: $name, props: $input) {
                    ok msg project {$fields}
                }
            }
        """
        )
        resolved_fields = resolve_fields(
            fields,
            project_fields,
            (project_fields["id"], project_fields["domain_name"], project_fields["name"]),
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
        return data["create_project"]

    @api_function
    @classmethod
    async def update(
        cls,
        pid: str,
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
        Update existing project.
        You need an admin privilege for this operation.
        """
        query = textwrap.dedent(
            """\
            mutation($pid: UUID!, $input: ModifyProjectInput!) {
                modify_project(pid: $pid, props: $input) {
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
            "pid": pid,
            "input": inputs,
        }
        data = await api_session.get().Admin._query(query, variables)
        return data["modify_project"]

    @api_function
    @classmethod
    async def delete(cls, pid: str):
        """
        Inactivates the existing project. Does not actually delete it for safety.
        """
        query = textwrap.dedent(
            """\
            mutation($pid: UUID!) {
                delete_project(pid: $pid) {
                    ok msg
                }
            }
        """
        )
        variables = {"pid": pid}
        data = await api_session.get().Admin._query(query, variables)
        return data["delete_project"]

    @api_function
    @classmethod
    async def purge(cls, pid: str):
        """
        Delete the existing project. This action cannot be undone.
        """
        query = textwrap.dedent(
            """\
            mutation($pid: UUID!) {
                purge_project(pid: $pid) {
                    ok msg
                }
            }
        """
        )
        variables = {"pid": pid}
        data = await api_session.get().Admin._query(query, variables)
        return data["purge_project"]

    @api_function
    @classmethod
    async def add_users(
        cls, pid: str, user_uuids: Iterable[str], fields: Iterable[FieldSpec | str] = None
    ) -> dict:
        """
        Add users to a project.
        You need an admin privilege for this operation.
        """
        query = textwrap.dedent(
            """\
            mutation($pid: UUID!, $input: ModifyProjectInput!) {
                modify_project(pid: $pid, props: $input) {
                    ok msg
                }
            }
        """
        )
        variables = {
            "pid": pid,
            "input": {
                "user_update_mode": "add",
                "user_uuids": user_uuids,
            },
        }
        data = await api_session.get().Admin._query(query, variables)
        return data["modify_project"]

    @api_function
    @classmethod
    async def remove_users(
        cls, pid: str, user_uuids: Iterable[str], fields: Iterable[FieldSpec | str] = None
    ) -> dict:
        """
        Remove users from a project.
        You need an admin privilege for this operation.
        """
        query = textwrap.dedent(
            """\
            mutation($pid: UUID!, $input: ModifyProjectInput!) {
                modify_project(pid: $pid, props: $input) {
                    ok msg
                }
            }
        """
        )
        variables = {
            "pid": pid,
            "input": {
                "user_update_mode": "remove",
                "user_uuids": user_uuids,
            },
        }
        data = await api_session.get().Admin._query(query, variables)
        return data["modify_project"]
