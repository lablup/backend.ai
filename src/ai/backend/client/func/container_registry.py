from __future__ import annotations

from ai.backend.client.request import Request
from ai.backend.common.container_registry import (
    PatchContainerRegistryRequestModel,
    PatchContainerRegistryResponseModel,
)

from .base import BaseFunction, api_function

__all__ = ("ContainerRegistry",)


class ContainerRegistry(BaseFunction):
    """
    Provides functions to manage container registries.
    """

    @api_function
    @classmethod
    async def patch_container_registry(
        cls, registry_id: str, params: PatchContainerRegistryRequestModel
    ) -> PatchContainerRegistryResponseModel:
        """
        Updates the container registry information, and return the container registry.

        :param registry_id: ID of the container registry.
        :param params: Parameters to update the container registry.
        """

        request = Request(
            "PATCH",
            f"/container-registries/{registry_id}",
        )
        request.set_json(params)

        async with request.fetch() as resp:
            return await resp.json()
