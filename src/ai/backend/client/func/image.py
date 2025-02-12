from typing import Optional, Sequence

from ai.backend.client.output.fields import image_fields
from ai.backend.client.output.types import FieldSpec

from ..request import Request
from ..session import api_session
from ..utils import dedent as _d
from .base import BaseFunction, api_function

__all__ = ("Image",)

_default_list_fields_admin = (
    image_fields["name"],
    image_fields["registry"],
    image_fields["architecture"],
    image_fields["tag"],
    image_fields["digest"],
    image_fields["size_bytes"],
    image_fields["aliases"],
)


class Image(BaseFunction):
    """
    Provides a shortcut of :func:`Admin.query()
    <ai.backend.client.admin.Admin.query>` that fetches the information about
    available images.
    """

    @api_function
    @classmethod
    async def list(
        cls,
        operation: bool = False,
        fields: Sequence[FieldSpec] = _default_list_fields_admin,
    ) -> Sequence[dict]:
        """
        Fetches the list of registered images in this cluster.
        """
        q = _d("""
            query($is_operation: Boolean) {
                images(is_operation: $is_operation) {
                    $fields
                }
            }
        """)
        q = q.replace("$fields", " ".join(f.field_ref for f in fields))
        variables = {
            "is_operation": operation,
        }
        data = await api_session.get().Admin._query(q, variables)
        return data["images"]

    @api_function
    @classmethod
    async def get(
        cls,
        reference: str,
        architecture: str,
        fields: Sequence[FieldSpec] = _default_list_fields_admin,
    ) -> Sequence[dict]:
        """
        Fetches the information about registered image in this cluster.
        """
        q = _d("""
            query($reference: String!, $architecture: String!) {
                image(reference: $reference, architecture: $architecture) {
                    $fields"
                }
            }
        """)
        q = q.replace("$fields", " ".join(f.field_ref for f in fields))
        variables = {
            "reference": reference,
            "architecture": architecture,
        }
        data = await api_session.get().Admin._query(q, variables)
        return data["image"]

    @api_function
    @classmethod
    async def get_by_id(
        cls,
        id: str,
        fields: Sequence[FieldSpec] = _default_list_fields_admin,
    ) -> Sequence[dict]:
        """
        Fetches the information about registered image in this cluster.
        """
        q = _d("""
            query($id: String!) {
                image(id: $id) {
                    $fields
                }
            }
        """)
        q = q.replace("$fields", " ".join(f.field_ref for f in fields))
        variables = {
            "id": id,
        }
        data = await api_session.get().Admin._query(q, variables)
        return data["image"]

    @api_function
    @classmethod
    async def list_customized(
        cls,
        fields: Sequence[FieldSpec] = _default_list_fields_admin,
    ) -> Sequence[dict]:
        """
        Fetches the list of customized images in this cluster.
        """
        q = _d("""
            query {
                customized_images {
                    $fields
                }
            }
        """)
        q = q.replace("$fields", " ".join(f.field_ref for f in fields))
        data = await api_session.get().Admin._query(q, {})
        return data["customized_images"]

    @api_function
    @classmethod
    async def rescan_images(cls, registry: str, project: Optional[str] = None):
        q = _d("""
            mutation($registry: String, $project: String) {
                rescan_images(registry:$registry, project: $project) {
                   ok msg task_id
                }
            }
        """)

        variables = {
            "registry": registry,
            "project": project,
        }

        data = await api_session.get().Admin._query(q, variables)
        return data["rescan_images"]

    @api_function
    @classmethod
    async def forget_image_by_id(cls, image_id: str):
        q = _d("""
            mutation($image_id: String!) {
                forget_image_by_id(image_id: $image_id) {
                    ok msg
                }
            }
        """)
        variables = {
            "image_id": image_id,
        }
        data = await api_session.get().Admin._query(q, variables)
        return data["forget_image_by_id"]

    @api_function
    @classmethod
    async def untag_image_from_registry(cls, id: str):
        q = _d("""
            mutation($id: String!) {
                untag_image_from_registry(id: $id) {
                    ok msg
                }
            }
        """)
        variables = {
            "id": id,
        }
        data = await api_session.get().Admin._query(q, variables)
        return data["untag_image_from_registry"]

    @api_function
    @classmethod
    async def forget_image(cls, reference: str, architecture: str):
        q = _d("""
            mutation($reference: String!, $architecture: String!) {
                forget_image(reference: $reference, architecture: $architecture) {
                   ok msg
                }
            }
        """)
        variables = {
            "reference": reference,
            "architecture": architecture,
        }
        data = await api_session.get().Admin._query(q, variables)
        return data["forget_image"]

    @api_function
    @classmethod
    async def alias_image(
        cls,
        alias: str,
        target: str,
        arch: Optional[str] = None,
    ) -> dict:
        q = _d("""
            mutation($alias: String!, $target: String!) {
                alias_image(alias: $alias, target: $target) {
                   ok msg
                }
            }
        """)
        variables = {
            "alias": alias,
            "target": target,
        }
        if arch:
            variables = {"architecture": arch, **variables}
        data = await api_session.get().Admin._query(q, variables)
        return data["alias_image"]

    @api_function
    @classmethod
    async def dealias_image(cls, alias: str) -> dict:
        q = _d("""
            mutation($alias: String!) {
                dealias_image(alias: $alias) {
                    ok msg
                }
            }
        """)
        variables = {
            "alias": alias,
        }
        data = await api_session.get().Admin._query(q, variables)
        return data["dealias_image"]

    @api_function
    @classmethod
    async def get_image_import_form(cls) -> dict:
        rqst = Request("GET", "/image/import")
        async with rqst.fetch() as resp:
            data = await resp.json()
        return data

    @api_function
    @classmethod
    async def build(cls, **kwargs) -> dict:
        rqst = Request("POST", "/image/import")
        rqst.set_json(kwargs)
        async with rqst.fetch() as resp:
            data = await resp.json()
        return data
