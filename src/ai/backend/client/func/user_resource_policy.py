from collections.abc import Sequence
from typing import Optional

from ..output.fields import user_resource_policy_fields
from ..output.types import FieldSpec
from ..session import api_session
from ..utils import dedent as _d
from .base import BaseFunction, api_function

_default_list_fields = (
    user_resource_policy_fields["name"],
    user_resource_policy_fields["max_vfolder_count"],
    user_resource_policy_fields["max_quota_scope_size"],
    user_resource_policy_fields["max_session_count_per_model_session"],
    user_resource_policy_fields["max_customized_image_count"],
)

_default_detail_fields = (
    user_resource_policy_fields["name"],
    user_resource_policy_fields["max_vfolder_count"],
    user_resource_policy_fields["max_quota_scope_size"],
    user_resource_policy_fields["max_session_count_per_model_session"],
    user_resource_policy_fields["max_customized_image_count"],
)


class UserResourcePolicy(BaseFunction):
    """
    Provides interactions with user resource policy.
    """

    _name: Optional[str]

    def __init__(self, name: Optional[str]) -> None:
        super().__init__()
        self._name = name

    @api_function
    @classmethod
    async def create(
        cls,
        name: str,
        *,
        max_vfolder_count: int,
        max_quota_scope_size: int,
        max_session_count_per_model_session: int,
        max_customized_image_count: int,
    ) -> dict:
        """
        Create a new user resource policy.

        :param name: Name of the user resource policy.
        :param max_vfolder_count: Maximum number of vfolders allowed.
        :param max_quota_scope_size: Maximum size of the quota scope (-1 for unlimited).
        :param max_session_count_per_model_session: Maximum session count per model service.
        :param max_customized_image_count: Maximum number of customized images allowed.
        :return: The created user resource policy data.
        """
        q = _d("""
            mutation($name: String!, $input: CreateUserResourcePolicyInput!) {
                create_user_resource_policy(name: $name, props: $input) {
                        ok
                        msg
                    }
            }
        """)

        input = {
            "max_vfolder_count": max_vfolder_count,
            "max_quota_scope_size": max_quota_scope_size,
            "max_session_count_per_model_session": max_session_count_per_model_session,
            "max_customized_image_count": max_customized_image_count,
        }

        result = await api_session.get().Admin._query(
            q,
            variables={
                "name": name,
                "input": input,
            },
        )

        return result["create_user_resource_policy"]

    @api_function
    @classmethod
    async def update(
        cls,
        name: str,
        *,
        max_vfolder_count: Optional[int] = None,
        max_quota_scope_size: Optional[int] = None,
        max_session_count_per_model_session: Optional[int] = None,
        max_customized_image_count: Optional[int] = None,
    ) -> dict:
        """
        Update an existing user resource policy with the given options.

        :param name: Name of the user resource policy to update.
        :param max_vfolder_count: New maximum number of vfolders allowed.
        :param max_quota_scope_size: New maximum size of the quota scope (-1 for unlimited).
        :param max_session_count_per_model_session: New maximum session count per model service.
        :param max_customized_image_count: New maximum number of customized images allowed.
        :return: The updated user resource policy data.
        """
        q = _d("""
            mutation($name: String!, $input: ModifyUserResourcePolicyInput!) {
                modify_user_resource_policy(name: $name, props: $input) {
                    ok
                }
            }
        """)

        input = {
            "max_vfolder_count": max_vfolder_count,
            "max_quota_scope_size": max_quota_scope_size,
            "max_session_count_per_model_session": max_session_count_per_model_session,
            "max_customized_image_count": max_customized_image_count,
        }

        variables = {
            "name": name,
            "input": {k: v for k, v in input.items() if v is not None},
        }

        result = await api_session.get().Admin._query(q, variables)
        return result["modify_user_resource_policy"]

    @api_function
    async def delete(self) -> dict:
        """
        Delete an existing user resource policy.
        :return: Result of the deletion operation.
        """
        q = _d("""
            mutation($name: String!) {
                delete_user_resource_policy(name: $name) {
                    ok
                    msg
                }
            }
        """)

        result = await api_session.get().Admin._query(q, {"name": self._name})
        return result["delete_user_resource_policy"]

    @api_function
    @classmethod
    async def list(
        cls,
        fields: Sequence[FieldSpec] = _default_list_fields,
    ) -> Sequence[dict]:
        """
        Lists all user resource policies.

        :param fields: Fields to include in the output.
        :return: List of user resource policies.
        """
        q = "query { user_resource_policies { $fields } }"
        q = q.replace("$fields", " ".join(f.field_ref for f in fields))
        data = await api_session.get().Admin._query(q)
        return data["user_resource_policies"]

    @api_function
    async def get_info(
        self,
        fields: Sequence[FieldSpec] = _default_detail_fields,
    ) -> dict:
        """
        Get information about a specific user resource policy.

        :param name: Name of the user resource policy to retrieve.
        :param fields: Fields to include in the output.
        :return: The user resource policy data.
        """
        q = "query($name: String!) { user_resource_policy(name: $name) { $fields } }"
        q = q.replace("$fields", " ".join(f.field_ref for f in fields))
        data = await api_session.get().Admin._query(q, {"name": self._name})
        return data["user_resource_policy"]
