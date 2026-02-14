from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from ai.backend.manager.dependencies.domain.distributed_lock import (
    DistributedLockFactoryDependency,
    DistributedLockInput,
    create_lock_factory,
)


@dataclass
class MockManagerConfig:
    ipc_base_path: Path
    id: str
    distributed_lock: str
    redlock_config: dict[str, Any]


@dataclass
class MockRedisConfig:
    pass


@dataclass
class MockUnifiedConfig:
    manager: MockManagerConfig
    redis: MockRedisConfig


@dataclass
class MockConfigProvider:
    config: MockUnifiedConfig


def _make_config_provider(lock_backend: str) -> MockConfigProvider:
    return MockConfigProvider(
        config=MockUnifiedConfig(
            manager=MockManagerConfig(
                ipc_base_path=Path("/tmp/test"),
                id="test-manager",
                distributed_lock=lock_backend,
                redlock_config={"lock_retry_interval": 0.1},
            ),
            redis=MockRedisConfig(),
        ),
    )


class TestCreateLockFactory:
    """Test create_lock_factory pure function."""

    def test_filelock_backend(self) -> None:
        """Should create a filelock factory."""
        config_provider = _make_config_provider("filelock")
        db = MagicMock()
        etcd = MagicMock()

        factory = create_lock_factory(config_provider, db, etcd)  # type: ignore[arg-type]
        assert callable(factory)

    def test_pg_advisory_backend(self) -> None:
        """Should create a pg_advisory factory."""
        config_provider = _make_config_provider("pg_advisory")
        db = MagicMock()
        etcd = MagicMock()

        factory = create_lock_factory(config_provider, db, etcd)  # type: ignore[arg-type]
        assert callable(factory)

    @patch("ai.backend.manager.dependencies.domain.distributed_lock.redis_helper")
    def test_redlock_backend(self, mock_redis_helper: MagicMock) -> None:
        """Should create a redlock factory."""
        config_provider = _make_config_provider("redlock")
        mock_redis_target = MagicMock()
        config_provider.config.redis.to_redis_profile_target = MagicMock(  # type: ignore[attr-defined]
            return_value=mock_redis_target
        )
        db = MagicMock()
        etcd = MagicMock()

        factory = create_lock_factory(config_provider, db, etcd)  # type: ignore[arg-type]
        assert callable(factory)
        mock_redis_helper.get_redis_object_for_lock.assert_called_once()

    def test_etcd_backend(self) -> None:
        """Should create an etcd lock factory."""
        config_provider = _make_config_provider("etcd")
        db = MagicMock()
        etcd = MagicMock()

        factory = create_lock_factory(config_provider, db, etcd)  # type: ignore[arg-type]
        assert callable(factory)

    def test_invalid_backend_raises_error(self) -> None:
        """Should raise ValueError for unknown backends."""
        config_provider = _make_config_provider("invalid")
        db = MagicMock()
        etcd = MagicMock()

        with pytest.raises(ValueError, match="Invalid lock backend: invalid"):
            create_lock_factory(config_provider, db, etcd)  # type: ignore[arg-type]


class TestDistributedLockFactoryDependency:
    """Test DistributedLockFactoryDependency lifecycle."""

    @pytest.mark.asyncio
    @patch("ai.backend.manager.dependencies.domain.distributed_lock.create_lock_factory")
    async def test_provide_lock_factory(self, mock_create: MagicMock) -> None:
        """Dependency should create and yield a lock factory."""
        mock_factory = MagicMock()
        mock_create.return_value = mock_factory

        config_provider = MagicMock()
        db = MagicMock()
        etcd = MagicMock()

        dependency = DistributedLockFactoryDependency()
        lock_input = DistributedLockInput(
            config_provider=config_provider,
            db=db,
            etcd=etcd,
        )

        async with dependency.provide(lock_input) as factory:
            assert factory is mock_factory
            mock_create.assert_called_once_with(
                config_provider=config_provider,
                db=db,
                etcd=etcd,
            )

    def test_stage_name(self) -> None:
        """Dependency should have correct stage name."""
        dependency = DistributedLockFactoryDependency()
        assert dependency.stage_name == "distributed-lock-factory"
