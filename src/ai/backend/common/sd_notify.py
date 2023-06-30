"""
A wrapper for systemd's daemon status notification protocol.
The methods will silently becomes no-op if NOTIFY_SOCKET environment variable is not set.

This module implements a subset of the notification protocol, excluding
file descriptor related messages.

Reference: https://www.freedesktop.org/software/systemd/man/sd_notify.html

Usage:

.. code-block::

    import asyncio
    import sd_notify

    sdnotify = sd_notify.Notifier()

    # Report a status message
    await sdnotify.update_status("Initialising my service...")
    await asyncio.sleep(3)

    # Report that the program init is complete
    await sdnotify.ready()
    await sdnotify.update_status("Waiting for web requests...")
    await asyncio.sleep(3)

    # Report an error to the service manager
    await sdnotify.set_watchdog_error("An irrecoverable error occured!")
"""

from __future__ import annotations

import asyncio
import os
import socket

import asyncudp


class SystemdNotifier:
    socket: asyncudp.Socket | None
    address: str | None

    def __init__(self) -> None:
        self.socket = None
        self.address = os.getenv("NOTIFY_SOCKET", None)

    @property
    def enabled(self) -> bool:
        return self.address is not None

    async def _send(self, raw_msg: bytes) -> None:
        """
        Send a binary message via the notification socket.
        If the `NOTIFY_SOCKET` environment variable is not set,
        it will silently skip.
        """
        if self.address is None:
            return
        loop = asyncio.get_running_loop()
        if self.socket is None:
            self.socket = asyncudp.Socket(
                *(
                    await loop.create_datagram_endpoint(
                        asyncudp._SocketProtocol,
                        family=socket.AF_UNIX,
                        remote_addr=self.address,  # type: ignore
                    )
                ),
            )
        self.socket.sendto(raw_msg)

    async def ready(self) -> None:
        """Report ready service state, i.e., completed initialization."""
        await self._send(b"READY=1\n")

    async def stopping(self) -> None:
        """Report the stopping/shutting-down service state."""
        await self._send(b"STOPPING=1\n")

    async def reloading(self) -> None:
        """Report the reloading service state."""
        await self._send(b"RELOADING=1\n")

    async def set_errno(self, errno: int) -> None:
        """Set an errno-style integer code to indicate service failure."""
        await self._send(b"ERRNO=%d\n" % (errno,))

    async def set_buserror(self, code: str) -> None:
        """Set a D-Bus-style error code to indicate service failure."""
        await self._send(b"BUSERROR=%s\n" % (code.encode("utf8"),))

    async def set_main_pid(self, pid: int) -> None:
        """Set the main PID for the case when the service manager did not fork the process itself."""
        await self._send(b"MAINPID=%d\n" % (pid,))

    async def update_status(self, msg: str) -> None:
        """Set a custom service status message"""
        await self._send(b"STATUS=%s\n" % (msg.encode("utf8"),))

    async def keepalive(self) -> None:
        """
        Send a keepalive message to extend the watchdog timestamp.
        If the time that this keepalive message is not sent to systemd exceeds the watchdog
        timeout (WatchdogSec) then systemd will try to restart the service depending on
        the service configuration.
        """
        await self._send(b"WATCHDOG=1\n")

    async def trigger_watchdog(self, msg: str = None) -> None:
        """
        Triggers the systemd's watchdog handler immediately.

        If `msg` is specified, it will be reported as a custom status message to the
        service manager to provide more information.
        """
        if msg:
            await self.update_status(msg)
        await self._send(b"WATCHDOG=trigger\n")
