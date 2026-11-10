"""V2 SDK client for the merged app config domain."""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

from ai.backend.client.v2.base_domain import BaseDomainClient
from ai.backend.common.dto.manager.v2.app_config.request import (
    MyGetAppConfigsInput,
    PublicGetAppConfigsInput,
)
from ai.backend.common.dto.manager.v2.app_config.response import GetAppConfigsPayload

if TYPE_CHECKING:
    from ai.backend.client.v2.base_client import BackendAIAnonymousClient, BackendAIAuthClient

_PATH: Final = "/v2/app-config"


class V2AppConfigClient(BaseDomainClient):
    """SDK client for the merged app config read.

    An app config is not stored as such — it is the deep merge of every fragment visible to
    the caller, so this domain reads and never writes. Writes go through the fragment client.
    """

    _anon_client: BackendAIAnonymousClient

    def __init__(self, client: BackendAIAuthClient, anon_client: BackendAIAnonymousClient) -> None:
        super().__init__(client)
        self._anon_client = anon_client

    async def my_get_app_configs(self, request: MyGetAppConfigsInput) -> GetAppConfigsPayload:
        """Read the acting user's merged config for each of the requested names.

        The answer holds one entry per requested name, in the order they were given; a name
        nothing visible contributes to comes back with an empty merge.
        """
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/my/get",
            request=request,
            response_model=GetAppConfigsPayload,
        )

    async def public_get_app_configs(
        self, request: PublicGetAppConfigsInput
    ) -> GetAppConfigsPayload:
        """Read the merged config built from public fragments only.

        Sent over the unauthenticated client on purpose: this is the pre-login read, so it
        has to work for a caller that holds no credentials yet.
        """
        return await self._anon_client.typed_request(
            "POST",
            f"{_PATH}/public/get",
            request=request,
            response_model=GetAppConfigsPayload,
        )
