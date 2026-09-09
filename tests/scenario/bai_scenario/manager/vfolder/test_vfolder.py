"""VFolder scenarios: create -> get -> delete, with the storage proxy as a typed fake."""

from __future__ import annotations

from typing import override

import aiohttp
import pytest
from bai_kit.manager.fakes.storage_proxy import (
    FakeStorageProxyManagerFacingClient,
    StorageScript,
)
from bai_kit.manager.personas import MEMBER
from bai_kit.manager.wiring.vfolder import vfolder_wiring
from multidict import CIMultiDict, CIMultiDictProxy
from yarl import URL

from ai.backend.common.dto.manager.v2.vfolder.request import CreateVFolderInput
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.errors.storage import VFolderCreationFailure
from ai.backend.testutils.scenario import (
    Call,
    Runner,
    Scenario,
    Setup,
    Step,
    StepContext,
    all_of,
    contains,
    has,
    length,
    on_extra,
    scenario_id,
)

WIRING = vfolder_wiring

ENFORCEMENT_OFF = Setup(config={"manager.rbac.enforcement_enabled": False})


def _storage_refusal() -> aiohttp.ClientResponseError:
    """What the storage proxy client raises when the host answers 500."""
    url = URL("http://storage.invalid/folder/create")
    return aiohttp.ClientResponseError(
        request_info=aiohttp.RequestInfo(
            url=url, method="POST", headers=CIMultiDictProxy(CIMultiDict()), real_url=url
        ),
        history=(),
        status=500,
        message="disk full",
    )


class RefusingStorage(FakeStorageProxyManagerFacingClient):
    """Alternative 2 for scripting the fake: a subclass per scenario."""

    @override
    async def create_folder(
        self,
        volume: str,
        vfid: str,
        max_quota_scope_size: int | None = None,
        mode: int | None = None,
    ) -> None:
        await super().create_folder(volume, vfid, max_quota_scope_size, mode)
        raise _storage_refusal()


def _get_created(ctx: StepContext) -> Call:
    return Call("get", ctx.results[0].vfolder.id)


def _delete_created(ctx: StepContext) -> Call:
    return Call("delete", ctx.results[0].vfolder.id)


SCENARIOS = [
    Scenario.ok(
        "member-creates-personal-vfolder",
        actor=MEMBER,
        setup=ENFORCEMENT_OFF,
        when=CreateVFolderInput(name="data"),
        then=all_of(
            has(
                vfolder=has(
                    host="local:volume1",
                    metadata=has(name="data"),
                    access_control=has(ownership_type="user"),
                )
            ),
            on_extra("storage", has(calls=contains(has(method="create_folder", volume="volume1")))),
        ),
    ),
    Scenario.error(
        "enforcement-on-blocks-member-personal-vfolder-without-roles",
        actor=MEMBER,
        when=CreateVFolderInput(name="denied"),
        then=NotEnoughPermission,
    ),
    Scenario.flow(
        "create-get-delete",
        actor=MEMBER,
        setup=ENFORCEMENT_OFF,
        steps=[
            Step(CreateVFolderInput(name="flow"), has(vfolder=has(metadata=has(name="flow")))),
            Step(_get_created, has(metadata=has(name="flow"), status="ready")),
            Step(
                _delete_created,
                all_of(
                    has(id=lambda v: v is not None),
                    # Soft delete parks the folder in the trash; storage is untouched.
                    on_extra("storage", has(calls=length(1))),
                ),
            ),
        ],
    ),
    Scenario.error(
        "storage-refusal-fails-create-via-script",
        actor=MEMBER,
        setup=Setup(
            config={"manager.rbac.enforcement_enabled": False},
            extras={"storage": StorageScript(create_folder=_storage_refusal())},
        ),
        when=CreateVFolderInput(name="refused"),
        then=VFolderCreationFailure,
    ),
    Scenario.error(
        "storage-refusal-fails-create-via-subclass",
        actor=MEMBER,
        setup=Setup(
            config={"manager.rbac.enforcement_enabled": False},
            extras={"storage": RefusingStorage},
        ),
        when=CreateVFolderInput(name="refused-too"),
        then=VFolderCreationFailure,
    ),
]


@pytest.mark.parametrize("s", SCENARIOS, ids=scenario_id)
async def test_vfolder(s: Scenario, run: Runner) -> None:
    await run(s)
