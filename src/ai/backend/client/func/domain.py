import textwrap
from typing import Any, Iterable, Sequence

from ...cli.types import Undefined, undefined
from ..output.fields import domain_fields
from ..output.types import FieldSpec
from ..session import api_session
from ..types import set_if_set
from .base import BaseFunction, api_function, resolve_fields

__all__ = ("Domain",)

_default_list_fields = (
    domain_fields["name"],
    domain_fields["description"],
    domain_fields["is_active"],
    domain_fields["created_at"],
    domain_fields["total_resource_slots"],
    domain_fields["allowed_vfolder_hosts"],
    domain_fields["allowed_docker_registries"],
    domain_fields["integration_id"],
)

_default_detail_fields = (
    domain_fields["name"],
    domain_fields["description"],
    domain_fields["is_active"],
    domain_fields["created_at"],
    domain_fields["total_resource_slots"],
    domain_fields["allowed_vfolder_hosts"],
    domain_fields["allowed_docker_registries"],
    domain_fields["integration_id"],
)


class Domain(BaseFunction):
    """
    Provides a shortcut of :func:`Admin.query()
    <ai.backend.client.admin.Admin.query>` that fetches various domain
    information.

    .. note::

      All methods in this function class require your API access key to
      have the *admin* privilege.
    """

    @api_function
    @classmethod
    async def list(
        cls,
        fields: Sequence[FieldSpec] = _default_list_fields,
    ) -> Sequence[dict]:
        """
        Fetches the list of domains.

        :param fields: Additional per-domain query fields to fetch.
        """
        query = textwrap.dedent(
            """\
            query {
                domains {$fields}
            }
        """
        )
        query = query.replace("$fields", " ".join(f.field_ref for f in fields))
        data = await api_session.get().Admin._query(query)
        return data["domains"]

    @api_function
    @classmethod
    async def detail(
        cls,
        name: str,
        fields: Sequence[FieldSpec] = _default_detail_fields,
    ) -> dict:
        """
        Fetch information of a domain with name.

        :param name: Name of the domain to fetch.
        :param fields: Additional per-domain query fields to fetch.
        """
        query = textwrap.dedent(
            """\
            query($name: String) {
                domain(name: $name) {$fields}
            }
        """
        )
        query = query.replace("$fields", " ".join(f.field_ref for f in fields))
        variables = {"name": name}
        data = await api_session.get().Admin._query(query, variables)
        return data["domain"]

    @api_function
    @classmethod
    async def create(
        cls,
        name: str,
        *,
        description: str = "",
        is_active: bool = True,
        total_resource_slots: str | Undefined = undefined,
        vfolder_host_perms: str | Undefined = undefined,  # JSON string
        allowed_docker_registries: Sequence[str] | Undefined = undefined,
        integration_id: str | Undefined = undefined,
        fields: Iterable[FieldSpec | str] | None = None,
    ) -> dict:
        """
        Creates a new domain with the given options.
        You need an admin privilege for this operation.
        """
        query = textwrap.dedent(
            """\
            mutation($name: String!, $input: DomainInput!) {
                create_domain(name: $name, props: $input) {
                    ok msg domain {$fields}
                }
            }
        """
        )
        resolved_fields = resolve_fields(fields, domain_fields, (domain_fields["name"],))
        query = query.replace("$fields", " ".join(resolved_fields))
        inputs = {
            "description": description,
            "is_active": is_active,
        }
        set_if_set(inputs, "total_resource_slots", total_resource_slots)
        set_if_set(inputs, "allowed_vfolder_hosts", vfolder_host_perms)
        set_if_set(inputs, "allowed_docker_registries", allowed_docker_registries)
        set_if_set(inputs, "integration_id", integration_id)
        variables = {
            "name": name,
            "input": inputs,
        }
        data = await api_session.get().Admin._query(query, variables)
        return data["create_domain"]

    @api_function
    @classmethod
    async def update(
        cls,
        name: str,
        *,
        new_name: str | Undefined = undefined,
        description: str | Undefined = undefined,
        is_active: bool | Undefined = undefined,
        total_resource_slots: str | Undefined = undefined,
        vfolder_host_perms: str | Undefined = undefined,  # JSON string
        allowed_docker_registries: Sequence[str] | Undefined = undefined,
        integration_id: str | Undefined = undefined,
        fields: Iterable[FieldSpec | str] | None = None,
    ) -> dict:
        """
        Update existing domain.
        You need an admin privilege for this operation.
        """
        query = textwrap.dedent(
            """\
            mutation($name: String!, $input: ModifyDomainInput!) {
                modify_domain(name: $name, props: $input) {
                    ok msg
                }
            }
        """
        )
        inputs: dict[str, Any] = {}
        set_if_set(inputs, "name", new_name)
        set_if_set(inputs, "description", description)
        set_if_set(inputs, "is_active", is_active)
        set_if_set(inputs, "total_resource_slots", total_resource_slots)
        set_if_set(inputs, "allowed_vfolder_hosts", vfolder_host_perms)
        set_if_set(inputs, "allowed_docker_registries", allowed_docker_registries)
        set_if_set(inputs, "integration_id", integration_id)
        variables = {
            "name": name,
            "input": inputs,
        }
        data = await api_session.get().Admin._query(query, variables)
        return data["modify_domain"]

    @api_function
    @classmethod
    async def delete(cls, name: str):
        """
        Inactivates an existing domain.
        """
        query = textwrap.dedent(
            """\
            mutation($name: String!) {
                delete_domain(name: $name) {
                    ok msg
                }
            }
        """
        )
        variables = {"name": name}
        data = await api_session.get().Admin._query(query, variables)
        return data["delete_domain"]

    @api_function
    @classmethod
    async def purge(cls, name: str):
        """
        Deletes an existing domain.
        """
        query = textwrap.dedent(
            """\
            mutation($name: String!) {
                purge_domain(name: $name) {
                    ok msg
                }
            }
        """
        )
        variables = {"name": name}
        data = await api_session.get().Admin._query(query, variables)
        return data["purge_domain"]
