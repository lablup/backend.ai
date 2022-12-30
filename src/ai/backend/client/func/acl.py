import textwrap
from typing import Sequence

from ai.backend.client.output.fields import permission_fields
from ai.backend.client.output.types import FieldSpec

from ..session import api_session
from .base import BaseFunction, api_function

__all__ = ("Permission",)

_default_list_fields = (permission_fields["vfolder_host_permission_list"],)


class Permission(BaseFunction):
    @api_function
    @classmethod
    async def list(
        cls,
        fields: Sequence[FieldSpec] = _default_list_fields,
    ) -> Sequence[str]:
        """
        Fetches the list of atomic permissions.

        :param fields: Additional permission query fields to fetch.
        """
        query = textwrap.dedent(
            """\
            query {
                vfolder_host_permissions {$fields}
            }
        """
        )
        query = query.replace("$fields", " ".join(f.field_ref for f in fields))
        data = await api_session.get().Admin._query(query)
        return data["vfolder_host_permissions"]
