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

        access_key, secret_access_key, region, type_ = (
            self.registry_info["access_key"],
            self.registry_info["secret_access_key"],
            self.registry_info["region"],
            self.registry_info["type"],
        )

        self.ecr_client = boto3.client(
            type_,
            region_name=region,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_access_key,
        )

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
                    response = client.describe_repositories(nextToken=next_token)
                else:
                    response = client.describe_repositories()

                for repo in response["repositories"]:
                    # TODO: Verify this logic
                    repo_id = (repo["repositoryUri"].split("/"))[1]
                    yield f"{repo_id}/{repo["repositoryName"]}"

                next_token = response.get("nextToken")

                if not next_token:
                    break
        except Exception as e:
            print(f"An error occurred: {e}")
