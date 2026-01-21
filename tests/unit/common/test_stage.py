from unittest.mock import AsyncMock

import pytest

from ai.backend.common.stage.types import Provisioner, ProvisionStage, SpecGenerator


class DummySpec:
    pass


class DummyResource:
    pass


@pytest.mark.asyncio
async def test_provisionstage_success():
    spec_gen = AsyncMock(spec=SpecGenerator)
    spec = DummySpec()
    spec_gen.wait_for_spec.return_value = spec

    provisioner = AsyncMock(spec=Provisioner)
    resource = DummyResource()
    provisioner.setup.return_value = resource

    stage = ProvisionStage(provisioner)
    await stage.setup(spec_gen)
    result = await stage.wait_for_resource()
    assert result is resource


@pytest.mark.asyncio
async def test_provisionstage_setup_failure():
    spec_gen = AsyncMock(spec=SpecGenerator)
    spec_gen.wait_for_spec.return_value = DummySpec()

    provisioner = AsyncMock(spec=Provisioner)
    provisioner.setup.side_effect = Exception("fail")

    stage = ProvisionStage(provisioner)
    await stage.setup(spec_gen)
    with pytest.raises(RuntimeError):
        await stage.wait_for_resource()


@pytest.mark.asyncio
async def test_provisionstage_teardown():
    spec_gen = AsyncMock(spec=SpecGenerator)
    spec = DummySpec()
    spec_gen.wait_for_spec.return_value = spec

    provisioner = AsyncMock(spec=Provisioner)
    resource = DummyResource()
    provisioner.setup.return_value = resource

    stage = ProvisionStage(provisioner)
    await stage.setup(spec_gen)
    await stage.wait_for_resource()
    await stage.teardown()
    provisioner.teardown.assert_awaited_once_with(resource)
    assert stage._resource is None


@pytest.mark.asyncio
async def test_provisionstage_teardown_without_resource():
    provisioner = AsyncMock(spec=Provisioner)
    stage = ProvisionStage(provisioner)
    await stage.teardown()
    provisioner.teardown.assert_not_called()
