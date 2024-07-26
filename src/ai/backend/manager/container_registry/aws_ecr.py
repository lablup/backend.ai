import logging
from typing import AsyncIterator

import aiohttp
import boto3

from ai.backend.common.logging import BraceStyleAdapter

from .base import (
    BaseContainerRegistry,
)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))  # type: ignore[name-defined]


class AWSElasticContainerRegistry(BaseContainerRegistry):
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
                    match type_:
                        case "ecr":
                            yield repo["repositoryName"]
                        case "ecr-public":
                            # repositoryUri format:
                            # public.ecr.aws/<registry_alias>/<repository>
                            registry_alias = (repo["repositoryUri"].split("/"))[1]
                            yield f"{registry_alias}/{repo["repositoryName"]}"
                        case _:
                            raise ValueError(f"Unknown registry type: {type_}")

                next_token = response.get("nextToken")

                if not next_token:
                    break
        except Exception as e:
            log.error(f"Error occurred: {e}")
