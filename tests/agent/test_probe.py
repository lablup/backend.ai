import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.agent.probe.monitor import ProbeMonitor, ProbeMonitorManager, ProbeStatus


# MockProbe is a mock class for Probe.
class MockProbe:
    def __init__(self):
        self.check = AsyncMock()


# MockReporter is a mock class for Reporter.
class MockReporter:
    def __init__(self):
        self.report = AsyncMock()


# MockProbeMonitor is a mock class for ProbeMonitor.
class MockProbeMonitor:
    def __init__(self):
        self.start = AsyncMock()
        self.stop = MagicMock()


@pytest.mark.asyncio
async def test_probe_monitor_success():
    probe = MockProbe()
    reporter = MockReporter()
    threshold = 3
    interval = 0.1
    timeout = 1

    # set the mock check method to return SUCCESS status
    probe.check.side_effect = [
        AsyncMock(status=ProbeStatus.SUCCESS),
        AsyncMock(status=ProbeStatus.SUCCESS),
        AsyncMock(status=ProbeStatus.SUCCESS),
        AsyncMock(status=ProbeStatus.FAILURE),  # the last check is FAILURE
    ]

    # create the monitor and run it asynchronously
    monitor = ProbeMonitor(probe, reporter, timeout, interval, threshold)
    asyncio.create_task(monitor.start())
    await asyncio.sleep(0.35)  # wait for the monitor to run 3 times
    monitor.stop()

    # check if the reporter.report method is called
    assert reporter.report.call_count == 0  # the reporter should not be called
    assert probe.check.call_count == 4  # check method should be called 4 times


@pytest.mark.asyncio
async def test_probe_monitor_failure_reporting(mocker):
    probe = MockProbe()
    reporter = MockReporter()
    threshold = 3
    interval = 0.1
    timeout = 1

    # set the mock check method to return FAILURE status
    probe.check.side_effect = [
        AsyncMock(status=ProbeStatus.FAILURE),
        AsyncMock(status=ProbeStatus.FAILURE),
        AsyncMock(status=ProbeStatus.FAILURE),
    ]

    # start the monitor and run it asynchronously
    monitor = ProbeMonitor(probe, reporter, timeout, interval, threshold)
    asyncio.create_task(monitor.start())
    await asyncio.sleep(0.25)  # wait for the monitor to run 3 times
    monitor.stop()

    # check if the reporter.report method is called
    assert reporter.report.call_count == 1
    assert probe.check.call_count == 3  # check method should be called 3 times


@pytest.mark.asyncio
async def test_register_monitor():
    manager = ProbeMonitorManager()
    monitor = MockProbeMonitor()
    key = "test_monitor"

    await manager.register(key, monitor)

    assert key in manager._monitors
    await asyncio.sleep(0.1)
    monitor.start.assert_awaited_once()


@pytest.mark.asyncio
async def test_deregister_monitor():
    manager = ProbeMonitorManager()
    monitor = MockProbeMonitor()
    key = "test_monitor"

    await manager.register(key, monitor)
    await manager.deregister(key)

    assert key not in manager._monitors
    monitor.stop.assert_called_once()


@pytest.mark.asyncio
async def test_double_register():
    manager = ProbeMonitorManager()
    monitor1 = MockProbeMonitor()
    monitor2 = MockProbeMonitor()
    key = "test_monitor"

    await manager.register(key, monitor1)
    await manager.register(key, monitor2)

    # only the first monitor should be registered
    assert key in manager._monitors
    assert manager._monitors[key] is monitor1
    await asyncio.sleep(0.1)
    monitor1.start.assert_awaited_once()
    monitor2.start.assert_not_awaited()
