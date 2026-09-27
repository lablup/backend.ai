import logging
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import aiohttp
import pytest
from pytest_mock import MockerFixture

from ai.backend.common.data.storage.registries.types import ModelTarget
from ai.backend.storage.services.artifacts.reservoir import (
    ReservoirService,
    ReservoirServiceArgs,
)

_TRACE_LEVEL = 5


class TestReservoirBatchImportFailureLog:
    @pytest.fixture
    def background_task_manager(self) -> MagicMock:
        manager = MagicMock()
        manager.start = AsyncMock(return_value=uuid4())
        return manager

    @pytest.fixture
    def service(self, background_task_manager: MagicMock) -> ReservoirService:
        return ReservoirService(
            ReservoirServiceArgs(
                background_task_manager=background_task_manager,
                event_producer=MagicMock(),
                storage_pool=MagicMock(),
                reservoir_registry_configs={},
                artifact_verifier_ctx=MagicMock(),
                manager_client_pool=MagicMock(),
                redis_client=MagicMock(),
            )
        )

    @pytest.mark.parametrize(
        ("status", "log_level"),
        [(404, _TRACE_LEVEL), (500, logging.ERROR), (403, logging.ERROR)],
    )
    async def test_only_remote_not_found_is_logged_below_error(
        self,
        service: ReservoirService,
        background_task_manager: MagicMock,
        mocker: MockerFixture,
        caplog: pytest.LogCaptureFixture,
        status: int,
        log_level: int,
    ) -> None:
        mocker.patch.object(
            service,
            "import_model",
            AsyncMock(side_effect=aiohttp.ClientResponseError(MagicMock(), (), status=status)),
        )
        await service.import_models_batch(
            registry_name="reservoir",
            models=[ModelTarget(model_id="missing-model")],
            storage_step_mappings={},
            pipeline=MagicMock(),
            artifact_revision_ids=[uuid4()],
        )
        run_batch = background_task_manager.start.await_args.args[0]
        reporter = MagicMock()
        reporter.update = AsyncMock()

        with caplog.at_level(_TRACE_LEVEL, logger="ai.backend.storage.services.artifacts"):
            await run_batch(reporter)

        failures = [r for r in caplog.records if r.__dict__.get("log_tag_model_id")]
        assert len(failures) == 1
        assert failures[0].levelno == log_level
