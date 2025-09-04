"""Valkey-based leader election manager for distributed systems."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from typing import Final

from ai.backend.common.clients.valkey_client.valkey_leader.client import ValkeyLeaderClient
from ai.backend.common.leader.base import AbstractLeaderElection, LeaderTask
from ai.backend.common.leader.exceptions import AlreadyStartedError
from ai.backend.common.logging import BraceStyleAdapter

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


@dataclass(frozen=True)
class ValkeyLeaderElectionConfig:
    """Configuration for Valkey-based leader election."""

    server_id: str
    leader_key: str = "leader:default"
    lease_duration: int = 30  # 30 seconds lease
    renewal_interval: float = 10.0  # Renew every 10 seconds
    failure_threshold: int = 3  # Number of consecutive failures before losing leadership


class ValkeyLeaderElection(AbstractLeaderElection):
    """
    Manages leader election for a server using Valkey/Redis.

    This class handles the leader election state and renewal loop,
    and manages LeaderTask instances that should run only on the leader.
    """

    _leader_client: Final[ValkeyLeaderClient]
    _config: Final[ValkeyLeaderElectionConfig]
    _is_leader: bool
    _stopped: bool
    _started: bool
    _election_task: asyncio.Task[None] | None
    _leader_tasks: list[LeaderTask]

    def __init__(
        self,
        leader_client: ValkeyLeaderClient,
        config: ValkeyLeaderElectionConfig,
    ) -> None:
        """
        Initialize the Valkey leader election manager.

        Args:
            leader_client: Valkey leader election client
            config: Leader election configuration
        """
        self._leader_client = leader_client
        self._config = config

        # State management
        self._is_leader = False
        self._stopped = False
        self._started = False
        self._election_task = None
        self._leader_tasks = []

    @property
    def is_leader(self) -> bool:
        """Check if this instance is currently the leader."""
        return self._is_leader

    @property
    def server_id(self) -> str:
        """Get the server ID."""
        return self._config.server_id

    def register_task(self, task: LeaderTask) -> None:
        """
        Register a task to run when this instance is the leader.
        Must be called before start().

        Args:
            task: Leader task to register

        Raises:
            RuntimeError: If called after start()
        """
        if self._started:
            raise AlreadyStartedError("Cannot register tasks after leader election has started")
        self._leader_tasks.append(task)
        log.info(f"Registered leader task: {task.__class__.__name__}")

    async def _try_acquire_or_renew_leadership(self) -> bool:
        return await self._leader_client.acquire_or_renew_leadership(
            server_id=self._config.server_id,
            leader_key=self._config.leader_key,
            lease_duration=self._config.lease_duration,
        )

    async def _election_loop(self) -> None:
        """
        Background task that continuously tries to acquire or renew leadership.
        """
        failure_count = 0

        while not self._stopped:
            was_leader = self._is_leader
            try:
                acquired = await self._try_acquire_or_renew_leadership()
                failure_count = 0
                if acquired:
                    if not was_leader:
                        self._is_leader = True
                        log.info(
                            f"Server {self._config.server_id} became the leader for {self._config.leader_key}"
                        )
                else:
                    if was_leader:
                        self._is_leader = False
                        log.info(
                            f"Server {self._config.server_id} lost leadership for {self._config.leader_key}"
                        )
            except Exception:
                failure_count += 1
                log.warning(
                    f"Error during leadership renewal for {self._config.leader_key} "
                    f"(failure {failure_count}/{self._config.failure_threshold})"
                )
                if failure_count >= self._config.failure_threshold:
                    # Too many failures, lose leadership
                    if self._is_leader:
                        log.warning(
                            f"Server {self._config.server_id} lost leadership for {self._config.leader_key} "
                            f"after {self._config.failure_threshold} consecutive failures"
                        )
                    self._is_leader = False
                    failure_count = 0  # Reset after losing leadership

            await asyncio.sleep(self._config.renewal_interval)

    async def start(self) -> None:
        """
        Start the leader election renewal loop and all registered tasks.
        """
        log.info(f"Starting Valkey leader election for server {self._config.server_id}")

        if self._started:
            raise AlreadyStartedError("Leader election already started")

        self._started = True
        self._stopped = False

        # Start leader election loop
        self._election_task = asyncio.create_task(self._election_loop())
        self._election_task.set_name(f"valkey-leader-election-{self._config.server_id}")

        # Start all registered leader tasks
        for task in self._leader_tasks:
            await task.start(self)  # Pass self as LeadershipChecker
            log.debug(f"Started leader task: {task.__class__.__name__}")

        log.info("Valkey leader election started")

    async def stop(self) -> None:
        """
        Stop the leader election, all tasks, and release leadership if held.
        """
        if self._stopped:
            log.debug("Leader election already stopped")
            return

        log.info(f"Stopping Valkey leader election for server {self._config.server_id}")
        self._stopped = True

        # Stop all registered leader tasks
        for task in self._leader_tasks:
            await task.stop()
            log.debug(f"Stopped leader task: {task.__class__.__name__}")

        # Stop election task
        if self._election_task and not self._election_task.done():
            try:
                self._election_task.cancel()
                await self._election_task
            except asyncio.CancelledError:
                pass
            self._election_task = None

        # Release leadership if held
        if self._is_leader:
            await self._leader_client.release_leadership(
                server_id=self._config.server_id,
                leader_key=self._config.leader_key,
            )
            self._is_leader = False
        log.info("Valkey leader election stopped")
