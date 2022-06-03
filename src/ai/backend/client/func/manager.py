from typing import Any

from .base import api_function, BaseFunction
from ..request import Request


class Manager(BaseFunction):
    """
    Provides controlling of the gateway/manager servers.

    .. versionadded:: 18.12
    """

    @api_function
    @classmethod
    async def status(cls):
        """
        Returns the current status of the configured API server.
        """
        rqst = Request('GET', '/manager/status')
        rqst.set_json({
            'status': 'running',
        })
        async with rqst.fetch() as resp:
            return await resp.json()

    @api_function
    @classmethod
    async def freeze(cls, force_kill: bool = False):
        """
        Freezes the configured API server.
        Any API clients will no longer be able to create new compute sessions nor
        create and modify vfolders/keypairs/etc.
        This is used to enter the maintenance mode of the server for unobtrusive
        manager and/or agent upgrades.

        :param force_kill: If set ``True``, immediately shuts down all running
            compute sessions forcibly. If not set, clients who have running compute
            session are still able to interact with them though they cannot create
            new compute sessions.
        """
        rqst = Request('PUT', '/manager/status')
        rqst.set_json({
            'status': 'frozen',
            'force_kill': force_kill,
        })
        async with rqst.fetch():
            pass

    @api_function
    @classmethod
    async def unfreeze(cls):
        """
        Unfreezes the configured API server so that it resumes to normal operation.
        """
        rqst = Request('PUT', '/manager/status')
        rqst.set_json({
            'status': 'running',
        })
        async with rqst.fetch():
            pass

    @api_function
    @classmethod
    async def get_announcement(cls):
        '''
        Get current announcement.
        '''
        rqst = Request('GET', '/manager/announcement')
        async with rqst.fetch() as resp:
            return await resp.json()

    @api_function
    @classmethod
    async def update_announcement(cls, enabled: bool = True, message: str = None):
        '''
        Update (create / delete) announcement.

        :param enabled: If set ``False``, delete announcement.
        :param message: Announcement message. Required if ``enabled`` is True.
        '''
        rqst = Request('POST', '/manager/announcement')
        rqst.set_json({
            'enabled': enabled,
            'message': message,
        })
        async with rqst.fetch():
            pass

    @api_function
    @classmethod
    async def scheduler_op(cls, op: str, args: Any):
        '''
        Perform a scheduler operation.

        :param op: The name of scheduler operation.
        :param args: Arguments specific to the given operation.
        '''
        rqst = Request('POST', '/manager/scheduler/operation')
        rqst.set_json({
            'op': op,
            'args': args,
        })
        async with rqst.fetch():
            pass
