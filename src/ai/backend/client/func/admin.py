from typing import Any, Mapping, Optional

from ..exceptions import BackendAPIError
from ..request import Request
from ..session import api_session
from .base import BaseFunction, api_function

__all__ = ("Admin",)


class Admin(BaseFunction):
    """
    Provides the function interface for making admin GraphQL queries.

    .. note::

      Depending on the privilege of your API access key, you may or may not
      have access to querying/mutating server-side resources of other
      users.
    """

    @api_function
    @classmethod
    async def query(
        cls,
        query: str,
        variables: Optional[Mapping[str, Any]] = None,
    ) -> Any:
        """
        Sends the GraphQL query and returns the response.

        :param query: The GraphQL query string.
        :param variables: An optional key-value dictionary
            to fill the interpolated template variables
            in the query.

        :returns: The object parsed from the response JSON string.
        """
        return await cls._query(query, variables)

    @classmethod
    async def _query(
        cls,
        query: str,
        variables: Optional[Mapping[str, Any]] = None,
    ) -> Any:
        """
        Internal async implementation of the query() method,
        which may be reused by other functional APIs to make GQL requests.
        """
        gql_query = {
            "query": query,
            "variables": variables if variables else {},
        }
        if api_session.get().api_version >= (6, "20210815"):
            rqst = Request("POST", "/admin/gql")
            rqst.set_json(gql_query)
            async with rqst.fetch() as resp:
                response = await resp.json()
                errors = response.get("errors", [])
                if errors:
                    raise BackendAPIError(
                        400,
                        reason="Bad request",
                        data={
                            "type": "https://api.backend.ai/probs/graphql-error",
                            "title": "GraphQL-generated error",
                            "data": errors,
                        },
                    )
                else:
                    return response["data"]
        else:
            rqst = Request("POST", "/admin/graphql")
            rqst.set_json(gql_query)
            async with rqst.fetch() as resp:
                return await resp.json()
