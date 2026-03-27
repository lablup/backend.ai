from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from ai.backend.client.request import Request

from .base import BaseFunction, api_function

__all__ = ("Resource",)


class Resource(BaseFunction):
    """
    Provides interactions with resource.
    """

    @api_function
    @classmethod
    async def list(cls) -> dict[str, Any]:
        """
        Lists all resource presets.
        """
        rqst = Request("GET", "/resource/presets")
        async with rqst.fetch() as resp:
            result: dict[str, Any] = await resp.json()

            return result

    @api_function
    @classmethod
    async def check_presets(cls, group: str | None = None, scaling_group: str | None = None) -> Any:
        """
        Lists all resource presets in the current scaling group with additional
        information.
        """
        rqst = Request("POST", "/resource/check-presets")
        data = {}
        if group is not None:
            data["group"] = group
        if scaling_group is not None:
            data["scaling_group"] = scaling_group
        rqst.set_json(data)
        async with rqst.fetch() as resp:
            result: dict[str, Any] = await resp.json()

            return result

    @api_function
    @classmethod
    async def get_docker_registries(cls) -> dict[str, Any]:
        """
        Lists all registered container registries.

        This API function is deprecated. Use `Resource.get_container_registries()` instead.
        """

        return await cls.get_container_registries()

    @api_function
    @classmethod
    async def get_container_registries(cls) -> dict[str, Any]:
        """
        Lists all registered container registries.
        """
        rqst = Request("GET", "/resource/container-registries")
        async with rqst.fetch() as resp:
            result: dict[str, Any] = await resp.json()

            return result

    @api_function
    @classmethod
    async def usage_per_month(cls, month: str, group_ids: Sequence[str]) -> dict[str, Any]:
        """
        Get usage statistics for groups specified by `group_ids` at specific `month`.

        :param month: The month you want to get the statistics (yyyymm).
        :param group_ids: Groups IDs to be included in the result.
        """
        rqst = Request(
            "GET",
            "/resource/usage/month",
            params={
                "group_ids": ",".join(group_ids),
                "month": month,
            },
        )

        async with rqst.fetch() as resp:
            result: dict[str, Any] = await resp.json()

            return result

    @api_function
    @classmethod
    async def usage_per_period(
        cls, group_id: str | None, start_date: str, end_date: str
    ) -> dict[str, Any]:
        """
        Get usage statistics for a group specified by `group_id` for time between
        `start_date` and `end_date`.

        :param start_date: start date in string format (yyyymmdd).
        :param end_date: end date in string format (yyyymmdd).
        :param group_id: Groups ID to list usage statistics.
        """
        params = {
            "start_date": start_date,
            "end_date": end_date,
        }
        if group_id is not None:
            params["group_id"] = group_id
        rqst = Request(
            "GET",
            "/resource/usage/period",
            params=params,
        )
        async with rqst.fetch() as resp:
            result: dict[str, Any] = await resp.json()

            return result

    @api_function
    @classmethod
    async def get_resource_slots(cls) -> dict[str, Any]:
        """
        Get supported resource slots of Backend.AI server.
        """
        rqst = Request("GET", "/config/resource-slots")
        async with rqst.fetch() as resp:
            result: dict[str, Any] = await resp.json()

            return result

    @api_function
    @classmethod
    async def get_vfolder_types(cls) -> dict[str, Any]:
        rqst = Request("GET", "/config/vfolder-types")
        async with rqst.fetch() as resp:
            result: dict[str, Any] = await resp.json()

            return result

    @api_function
    @classmethod
    async def recalculate_usage(cls) -> dict[str, Any]:
        rqst = Request("POST", "/resource/recalculate-usage")
        async with rqst.fetch() as resp:
            result: dict[str, Any] = await resp.json()

            return result

    @api_function
    @classmethod
    async def user_monthly_stats(cls) -> dict[str, Any]:
        rqst = Request("GET", "/resource/stats/user/month")
        async with rqst.fetch() as resp:
            result: dict[str, Any] = await resp.json()

            return result

    @api_function
    @classmethod
    async def admin_monthly_stats(cls) -> dict[str, Any]:
        rqst = Request("GET", "/resource/stats/admin/month")
        async with rqst.fetch() as resp:
            result: dict[str, Any] = await resp.json()

            return result
