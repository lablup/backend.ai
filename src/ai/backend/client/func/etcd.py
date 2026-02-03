from typing import Any, cast

from ai.backend.client.request import Request

from .base import BaseFunction, api_function

__all__ = ("EtcdConfig",)


class EtcdConfig(BaseFunction):
    """
    Provides a way to get or set ETCD configurations.

    .. note::

      All methods in this function class require your API access key to
      have the *superadmin* privilege.
    """

    @api_function
    @classmethod
    async def get(cls, key: str, prefix: bool = False) -> dict[str, Any]:
        """
        Get configuration from ETCD with given key.

        :param key: Name of the key to fetch.
        :param prefix: get all keys prefixed with the give key.
        """
        rqst = Request("POST", "/config/get")
        rqst.set_json({
            "key": key,
            "prefix": prefix,
        })
        async with rqst.fetch() as resp:
            data = await resp.json()
            return cast(dict[str, Any], data.get("result", None))

    @api_function
    @classmethod
    async def set(cls, key: str, value: str) -> dict[str, Any]:
        """
        Set configuration into ETCD with given key and value.

        :param key: Name of the key to set.
        :param value: Value to set.
        """
        rqst = Request("POST", "/config/set")
        rqst.set_json({
            "key": key,
            "value": value,
        })
        async with rqst.fetch() as resp:
            result: dict[str, Any] = await resp.json()

            return result

    @api_function
    @classmethod
    async def delete(cls, key: str, prefix: bool = False) -> dict[str, Any]:
        """
        Delete configuration from ETCD with given key.

        :param key: Name of the key to delete.
        :param prefix: delete all keys prefixed with the give key.
        """
        rqst = Request("POST", "/config/delete")
        rqst.set_json({
            "key": key,
            "prefix": prefix,
        })
        async with rqst.fetch() as resp:
            result: dict[str, Any] = await resp.json()

            return result
