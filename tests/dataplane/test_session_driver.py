"""Tests of the session driver, against a fake manager.

The driver is the piece every scenario stands on, so its own failure modes are worth pinning
before any scenario uses it: a wait that hangs instead of reporting, a teardown that is skipped
when the scenario fails, a terminal status that is mistaken for "not there yet".

No manager, no privileges — these run in ordinary CI.
"""

from __future__ import annotations

from typing import Any, override
from uuid import UUID, uuid4

import pytest

from ai.backend.common.dto.manager.v2.session.request import (
    EnqueueSessionInput,
    TerminateSessionsInput,
)
from ai.backend.common.dto.manager.v2.session.types import ClusterModeEnum
from ai.backend.testutils.dataplane.session import (
    SessionDriver,
    SessionSpec,
    SessionWaitTimeout,
    SessionWentWrong,
    kernel_ids_of,
    unique_name,
)

SESSION_ID = UUID("d4ec3a69-f03f-4ab7-8e66-341fbc5efb4c")


class FakeSessionApi:
    """Replays a scripted status sequence and records the calls made against it."""

    statuses: list[str]
    enqueued: list[EnqueueSessionInput]
    terminated: list[TerminateSessionsInput]
    _polls: int

    def __init__(self, statuses: list[str], *, session_id: UUID = SESSION_ID) -> None:
        self.statuses = statuses
        self.enqueued = []
        self.terminated = []
        self._polls = 0
        self._session_id = session_id

    async def enqueue(self, request: EnqueueSessionInput) -> dict[str, Any]:
        self.enqueued.append(request)
        # The REST payload nests the created session, which the driver has to see through.
        return {"session": {"id": str(self._session_id)}}

    async def get(self, session_id: UUID) -> dict[str, Any]:
        index = min(self._polls, len(self.statuses) - 1)
        self._polls += 1
        return {"lifecycle": {"status": self.statuses[index]}}

    async def terminate(self, request: TerminateSessionsInput) -> dict[str, Any]:
        self.terminated.append(request)
        return {"terminated": [str(self._session_id)]}


def _driver(api: FakeSessionApi) -> SessionDriver:
    return SessionDriver(api, interval=0, max_wait=10)


class TestSessionSpec:
    def test_two_kernels_on_one_node_is_expressible_without_manager_vocabulary(self) -> None:
        spec = SessionSpec(
            image_id=uuid4(),
            project_id=uuid4(),
            cluster_size=2,
            cluster_mode=ClusterModeEnum.SINGLE_NODE,
        )
        body = spec.to_enqueue_input("s1")
        assert body.cluster_size == 2
        assert body.cluster_mode is ClusterModeEnum.SINGLE_NODE
        assert body.session_name == "s1"

    def test_resource_entries_carry_cpu_and_mem(self) -> None:
        body = SessionSpec(image_id=uuid4(), project_id=uuid4()).to_enqueue_input("s1")
        assert {e.resource_type for e in body.resource_entries} == {"cpu", "mem"}

    def test_the_payload_is_the_managers_own_model_not_a_dict(self) -> None:
        """The client serializes with `request.model_dump()`, so a hand-written mapping fails at
        runtime rather than at the type checker -- and would drift from what the manager accepts."""
        body = SessionSpec(image_id=uuid4(), project_id=uuid4()).to_enqueue_input("s1")
        assert isinstance(body, EnqueueSessionInput)
        assert body.model_dump(mode="json", exclude_none=True)["session_name"] == "s1"


class TestCreate:
    async def test_waits_for_running(self) -> None:
        api = FakeSessionApi(["PENDING", "PREPARING", "CREATING", "RUNNING"])
        handle = await _driver(api).create(SessionSpec(uuid4(), uuid4()), "s1")
        assert handle.session_id == SESSION_ID
        assert handle.name == "s1"

    async def test_session_id_is_read_from_the_nested_payload(self) -> None:
        api = FakeSessionApi(["RUNNING"])
        handle = await _driver(api).create(SessionSpec(uuid4(), uuid4()), "s1")
        assert handle.session_id == SESSION_ID

    async def test_a_session_that_dies_while_waiting_fails_at_once(self) -> None:
        """CANCELLED is terminal. Burning the full bound before saying so only delays the same
        answer, and hides which status it actually reached."""
        api = FakeSessionApi(["PENDING", "CANCELLED"])
        with pytest.raises(SessionWentWrong, match="reached CANCELLED while waiting for RUNNING"):
            await _driver(api).create(SessionSpec(uuid4(), uuid4()), "s1")

    async def test_a_stuck_session_reports_the_status_it_was_stuck_in(self) -> None:
        """The failure this suite met on its first live run: CREATING forever. The message has to
        name CREATING, or it points nowhere."""
        api = FakeSessionApi(["CREATING"])
        with pytest.raises(SessionWaitTimeout, match="still CREATING"):
            await SessionDriver(api, interval=0, max_wait=0).create(
                SessionSpec(uuid4(), uuid4()), "s1"
            )


class TestDestroy:
    async def test_waits_for_terminated(self) -> None:
        api = FakeSessionApi(["TERMINATING", "TERMINATED"])
        await _driver(api).destroy(SESSION_ID)
        assert api.terminated[0].session_ids == [SESSION_ID]

    async def test_can_skip_the_wait(self) -> None:
        api = FakeSessionApi(["TERMINATING"])
        await _driver(api).destroy(SESSION_ID, wait=False)
        assert api.terminated


class TestSessionContextManager:
    async def test_destroys_on_success(self) -> None:
        api = FakeSessionApi(["RUNNING", "RUNNING", "TERMINATED"])
        async with _driver(api).session(SessionSpec(uuid4(), uuid4()), "s1"):
            pass
        assert api.terminated

    async def test_destroys_even_when_the_scenario_fails(self) -> None:
        """A scenario that raised mid-way is exactly when leaving a session behind would poison
        every later test's baseline."""
        api = FakeSessionApi(["RUNNING", "RUNNING", "TERMINATED"])
        with pytest.raises(ZeroDivisionError):
            async with _driver(api).session(SessionSpec(uuid4(), uuid4()), "s1"):
                raise ZeroDivisionError
        assert api.terminated


class TestPayloadShapes:
    async def test_missing_lifecycle_is_an_error_not_a_silent_default(self) -> None:
        class BadApi(FakeSessionApi):
            @override
            async def get(self, session_id: UUID) -> dict[str, Any]:
                return {"id": "x"}

        with pytest.raises(SessionWentWrong, match="no lifecycle"):
            await _driver(BadApi([])).status(SESSION_ID)

    def test_kernel_ids_from_a_mapping(self) -> None:
        assert kernel_ids_of({"kernels": [{"id": "k1"}, {"id": "k2"}]}) == ("k1", "k2")

    def test_kernel_ids_of_a_session_without_kernels(self) -> None:
        assert kernel_ids_of({"kernels": []}) == ()


class TestRunningIsNotFinal:
    """Regression: RUNNING was in the final-status set, so waiting for TERMINATED from a running
    session failed instantly and every teardown broke. A running session is a resting state, not
    an end state — it is precisely what `destroy` waits its way out of."""

    async def test_terminated_can_be_awaited_from_running(self) -> None:
        api = FakeSessionApi(["RUNNING", "RUNNING", "TERMINATING", "TERMINATED"])
        await _driver(api).destroy(SESSION_ID)
        assert api.terminated

    async def test_a_teardown_that_ends_cancelled_is_accepted(self) -> None:
        """A session torn down before it ever ran ends CANCELLED, and that is a success for the
        caller — not a failure to reach TERMINATED."""
        api = FakeSessionApi(["CANCELLED"])
        await _driver(api).destroy(SESSION_ID)

    async def test_waiting_for_running_still_fails_on_a_final_status(self) -> None:
        api = FakeSessionApi(["PENDING", "TERMINATED"])
        with pytest.raises(SessionWentWrong, match="reached TERMINATED"):
            await _driver(api).create(SessionSpec(uuid4(), uuid4()), "s1")


class TestNaming:
    def test_name_is_capped_at_the_managers_limit(self) -> None:
        assert len(unique_name("x" * 80, suffix="abc")) == 64
