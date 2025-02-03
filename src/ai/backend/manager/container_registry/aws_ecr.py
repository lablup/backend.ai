import logging
from typing import AsyncIterator, override

import aiohttp
import boto3

from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.exceptions import ContainerRegistryProjectEmpty

from .base import (
    BaseContainerRegistry,
)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))  # type: ignore[name-defined]


class AWSElasticContainerRegistry(BaseContainerRegistry):
    @override
    async def fetch_repositories(
        self,
        sess: aiohttp.ClientSession,
    ) -> AsyncIterator[str]:
        if not self.registry_info.project:
            raise ContainerRegistryProjectEmpty(self.registry_info.type, self.registry_info.project)

        access_key, secret_access_key, region, type_ = (
            self.registry_info.extra.get("access_key"),
            self.registry_info.extra.get("secret_access_key"),
            self.registry_info.extra.get("region"),
            self.registry_info.type,
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
                            if repo["repositoryName"].startswith(self.registry_info.project):
                                yield repo["repositoryName"]
                        case "ecr-public":
                            registry_alias = (repo["repositoryUri"].split("/"))[1]
                            if self.registry_info.project == registry_alias:
                                yield f"{registry_alias}/{repo['repositoryName']}"
                        case _:
                            raise ValueError(f"Unknown registry type: {type_}")

                next_token = response.get("nextToken")

                if not next_token:
                    break
        except Exception as e:
            log.error(f"Error occurred: {e}")
