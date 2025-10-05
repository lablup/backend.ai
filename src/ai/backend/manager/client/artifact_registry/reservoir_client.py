import uuid
from collections.abc import Mapping
from datetime import datetime
from typing import Any

import aiohttp
import yarl
from dateutil.tz import tzutc

from ai.backend.common.auth.utils import generate_signature
from ai.backend.manager.data.reservoir_registry.types import ReservoirRegistryData
from ai.backend.manager.dto.request import (
    DelegateScanArtifactsReq,
    SearchArtifactsReq,
)
from ai.backend.manager.dto.response import (
    DelegateScanArtifactsResponse,
    GetArtifactRevisionReadmeResponse,
    SearchArtifactsResponse,
)

_HASH_TYPE = "sha256"


class ReservoirRegistryClient:
    """
    Client used to connect from one manager to another.
    Used when connecting to a remote reservoir service.
    """

    _id: uuid.UUID
    _name: str
    _endpoint: str
    _access_key: str
    _secret_key: str
    _api_version: str

    def __init__(self, registry_data: ReservoirRegistryData):
        self._id = registry_data.id
        self._name = registry_data.name
        self._endpoint = registry_data.endpoint
        self._access_key = registry_data.access_key
        self._secret_key = registry_data.secret_key
        self._api_version = registry_data.api_version

    def _build_header(self, method: str, rel_url: str) -> Mapping[str, str]:
        date = datetime.now(tzutc())
        hdrs, _ = generate_signature(
            method=method,
            version=self._api_version,
            endpoint=yarl.URL(self._endpoint),
            date=date,
            rel_url=rel_url,
            content_type="application/json",
            access_key=self._access_key,
            secret_key=self._secret_key,
            hash_type=_HASH_TYPE,
        )

        return {
            "User-Agent": "Backend.AI Manager facing manager client",
            "Content-Type": "application/json",
            "X-BackendAI-Version": self._api_version,
            "Date": date.isoformat(),
            **hdrs,
        }

    async def _request(self, method: str, rel_url: str, **kwargs) -> Any:
        header = self._build_header(method=method, rel_url=rel_url)
        url = yarl.URL(self._endpoint) / rel_url.lstrip("/")
        async with aiohttp.ClientSession() as session:
            async with session.request(method, str(url), headers=header, **kwargs) as response:
                response.raise_for_status()
                return await response.json()

    async def delegate_scan_artifacts(
        self, req: DelegateScanArtifactsReq
    ) -> DelegateScanArtifactsResponse:
        resp = await self._request(
            "POST", "/artifact-registries/delegation/scan", json=req.model_dump(mode="json")
        )
        return DelegateScanArtifactsResponse.model_validate(resp)

    async def search_artifacts(self, req: SearchArtifactsReq) -> SearchArtifactsResponse:
        resp = await self._request(
            "POST", "/artifact-registries/search", json=req.model_dump(mode="json")
        )
        return SearchArtifactsResponse.model_validate(resp)

    async def get_readme(
        self, artifact_revision_id: uuid.UUID
    ) -> GetArtifactRevisionReadmeResponse:
        resp = await self._request("GET", f"/artifacts/revisions/{artifact_revision_id}/readme")
        return GetArtifactRevisionReadmeResponse.model_validate(resp)
