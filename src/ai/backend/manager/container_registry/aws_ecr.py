import base64
import logging
from typing import Any, AsyncIterator, Mapping

import aiohttp
import boto3

from ai.backend.common.logging import BraceStyleAdapter
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine

from .base import (
    BaseContainerRegistry,
)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))  # type: ignore[name-defined]


class AWSElasticContainerRegistry_v2(BaseContainerRegistry):
    @staticmethod
    def get_credential(registry_info: Mapping[str, Any]) -> dict[str, Any]:
        access_key, secret_access_key, region, type_ = (
            registry_info["access_key"],
            registry_info["secret_access_key"],
            registry_info["region"],
            registry_info["type"],
        )

        ecr_client = boto3.client(
            type_,
            region_name=region,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_access_key,
        )

        auth_token = ecr_client.get_authorization_token()["authorizationData"]["authorizationToken"]
        decoded_auth_token = base64.b64decode(auth_token).decode("utf-8")
        username, password = decoded_auth_token.split(":")

        return {"username": username, "password": password}

    def __init__(
        self,
        db: ExtendedAsyncSAEngine,
        registry_name: str,
        registry_info: Mapping[str, Any],
        *,
        max_concurrency_per_registry: int = 4,
        ssl_verify: bool = True,
    ) -> None:
        super().__init__(
            db,
            registry_name,
            registry_info,
            max_concurrency_per_registry=max_concurrency_per_registry,
            ssl_verify=ssl_verify,
        )

        self.credentials = AWSElasticContainerRegistry_v2.get_credential(registry_info)

    async def fetch_repositories(
        self,
        sess: aiohttp.ClientSession,
    ) -> AsyncIterator[str]:
        access_key, secret_access_key, region, type_ = (
            self.registry_info["access_key"],
            self.registry_info["secret_access_key"],
            self.registry_info["region"],
            self.registry_info["type"],
        )

        client = boto3.client(
            type_,
            region_name=region,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_access_key,
        )

        next_token = None
        try:
            while True:
                if next_token:
                    response = client.describe_repositories(nextToken=next_token, maxResults=30)
                else:
                    response = client.describe_repositories(maxResults=30)

                for repo in response["repositories"]:
                    registry_alias = (repo["repositoryUri"].split("/"))[1]
                    yield f"{registry_alias}/{repo["repositoryName"]}"

                next_token = response.get("nextToken")

                if not next_token:
                    break
        except Exception as e:
            log.error(f"Error occurred: {e}")
