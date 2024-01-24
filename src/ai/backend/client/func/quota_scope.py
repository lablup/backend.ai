import textwrap
from typing import Sequence

from .base import BaseFunction, api_function
from ..session import api_session
from ..output.fields import quota_scope_fields, user_fields, group_fields
from ..output.types import FieldSpec


_default_user_fields = (
    user_fields["uuid"],
    user_fields["username"],
)

_default_project_fields = (
    group_fields["id"],
    group_fields["name"],
)

_default_quota_scope_fields = (
    quota_scope_fields["usage_bytes"],
    quota_scope_fields["usage_count"],
    quota_scope_fields["hard_limit_bytes"]
)


class QuotaScope(BaseFunction):
    @api_function
    @classmethod
    async def get_user_qsid(
        cls,
        domain_name: str,
        email: str,
        fields: Sequence[FieldSpec] = _default_user_fields,
    ):
        query = textwrap.dedent(
            """\
            query($domain_name: String!, $email: String!) {
                user(domain_name: $domain_name, email: $email) {$fields}
            }
        """
        )
        query = query.replace("$fields", " ".join(f.field_ref for f in fields))
        variables = {
            "domain_name": domain_name,
            "email": email,
        }
        data = await api_session.get().Admin._query(query, variables)
        return data["user"]

    @api_function
    @classmethod
    async def get_project_qsid(
        cls,
        domain_name: str,
        name: str,
        fields: Sequence[FieldSpec] = _default_project_fields,
    ):
        query = textwrap.dedent(
            """\
            query($domain_name: String!, $name: String!) {
                groups_by_name(domain_name: $domain_name, name: $name) {$fields}
            }
        """
        )
        query = query.replace("$fields", " ".join(f.field_ref for f in fields))
        variables = {
            "domain_name": domain_name,
            "name": name,
        }
        data = await api_session.get().Admin._query(query, variables)
        return data["groups_by_name"][0]

    @api_function
    @classmethod
    async def get_quota_scope(
        cls,
        host: str,
        qsid: str,
        fields: Sequence[FieldSpec] = _default_quota_scope_fields,
    ):
        query = textwrap.dedent(
            """\
            query($storage_host_name: String!, $quota_scope_id: String!) {
                quota_scope(storage_host_name: $storage_host_name, quota_scope_id: $quota_scope_id) {details {$fields}}
            }
        """
        )
        query = query.replace("$fields", " ".join(f.field_ref for f in fields))
        variables = {
            "storage_host_name": host,
            "quota_scope_id": qsid,
        }
        data = await api_session.get().Admin._query(query, variables)
        return data["quota_scope"]['details']
