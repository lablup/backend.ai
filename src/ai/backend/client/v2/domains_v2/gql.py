"""V2 SDK client for raw GraphQL queries."""

from __future__ import annotations

from typing import Any, Final

from ai.backend.client.v2.base_domain import BaseDomainClient

_GQL_PATH_SESSION: Final = "/admin/gql"
_GQL_PATH_API_LEGACY: Final = "/admin/gql"
_GQL_PATH_API_V2: Final = "/admin/gql/strawberry"


class V2GQLClient(BaseDomainClient):
    """SDK client for sending raw GraphQL queries.

    When using session mode (webserver), both legacy (Graphene) and v2
    (Strawberry) schemas are served through a single unified endpoint
    via the hive router (Apollo Federation).

    When connecting directly to the manager (api mode), legacy and v2
    schemas live at separate paths.
    """

    def _gql_path(self, *, v2: bool = False) -> str:
        if self._client._config.endpoint_type == "session":
            return _GQL_PATH_SESSION
        return _GQL_PATH_API_V2 if v2 else _GQL_PATH_API_LEGACY

    async def query(
        self,
        query: str,
        variables: dict[str, Any] | None = None,
        *,
        v2: bool = False,
    ) -> dict[str, Any]:
        """Send a raw GraphQL query and return the JSON response.

        Args:
            query: The GraphQL query string.
            variables: Optional query variables.
            v2: When True and using direct API mode, target the Strawberry
                schema at ``/admin/gql/strawberry``. Ignored in session mode
                (hive router serves both schemas on a single endpoint).
        """
        body: dict[str, Any] = {"query": query}
        if variables:
            body["variables"] = variables
        result = await self._client._request("POST", self._gql_path(v2=v2), json=body)
        if result is None:
            return {}
        return dict(result) if isinstance(result, dict) else {"data": result}
