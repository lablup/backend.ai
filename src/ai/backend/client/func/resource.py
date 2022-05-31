from typing import Sequence

from .base import api_function, BaseFunction
from ..request import Request

__all__ = (
    'Resource'
)


class Resource(BaseFunction):
    """
    Provides interactions with resource.
    """

    @api_function
    @classmethod
    async def list(cls):
        """
        Lists all resource presets.
        """
        rqst = Request('GET', '/resource/presets')
        async with rqst.fetch() as resp:
            return await resp.json()

    @api_function
    @classmethod
    async def check_presets(cls):
        """
        Lists all resource presets in the current scaling group with additiona
        information.
        """
        rqst = Request('POST', '/resource/check-presets')
        async with rqst.fetch() as resp:
            return await resp.json()

    @api_function
    @classmethod
    async def get_docker_registries(cls):
        """
        Lists all registered docker registries.
        """
        rqst = Request('GET', '/config/docker-registries')
        async with rqst.fetch() as resp:
            return await resp.json()

    @api_function
    @classmethod
    async def usage_per_month(cls, month: str, group_ids: Sequence[str]):
        """
        Get usage statistics for groups specified by `group_ids` at specific `month`.

        :param month: The month you want to get the statistics (yyyymm).
        :param group_ids: Groups IDs to be included in the result.
        """
        rqst = Request('GET', '/resource/usage/month')
        rqst.set_json({
            'month': month,
            'group_ids': group_ids,
        })
        async with rqst.fetch() as resp:
            return await resp.json()

    @api_function
    @classmethod
    async def usage_per_period(cls, group_id: str, start_date: str, end_date: str):
        """
        Get usage statistics for a group specified by `group_id` for time betweeen
        `start_date` and `end_date`.

        :param start_date: start date in string format (yyyymmdd).
        :param end_date: end date in string format (yyyymmdd).
        :param group_id: Groups ID to list usage statistics.
        """
        rqst = Request('GET', '/resource/usage/period')
        rqst.set_json({
            'group_id': group_id,
            'start_date': start_date,
            'end_date': end_date,
        })
        async with rqst.fetch() as resp:
            return await resp.json()

    @api_function
    @classmethod
    async def get_resource_slots(cls):
        """
        Get supported resource slots of Backend.AI server.
        """
        rqst = Request('GET', '/config/resource-slots')
        async with rqst.fetch() as resp:
            return await resp.json()

    @api_function
    @classmethod
    async def get_vfolder_types(cls):
        rqst = Request('GET', '/config/vfolder-types')
        async with rqst.fetch() as resp:
            return await resp.json()

    @api_function
    @classmethod
    async def recalculate_usage(cls):
        rqst = Request('POST', '/resource/recalculate-usage')
        async with rqst.fetch() as resp:
            return await resp.json()

    @api_function
    @classmethod
    async def user_monthly_stats(cls):
        rqst = Request('GET', '/resource/stats/user/month')
        async with rqst.fetch() as resp:
            return await resp.json()

    @api_function
    @classmethod
    async def admin_monthly_stats(cls):
        rqst = Request('GET', '/resource/stats/admin/month')
        async with rqst.fetch() as resp:
            return await resp.json()
