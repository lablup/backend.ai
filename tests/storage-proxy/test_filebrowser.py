import uuid
from pathlib import PurePath

import pytest

from ai.backend.storage.vfs import BaseVolume


@pytest.fixture
async def vfs(local_volume):
    vfs = BaseVolume({}, local_volume, fsprefix=PurePath("fsprefix"), options={})
    await vfs.init()
    try:
        yield vfs
    finally:
        await vfs.shutdown()


@pytest.fixture
async def empty_vfolder(vfs):
    vfid = uuid.uuid4()
    await vfs.create_vfolder(vfid)
    yield vfid
    await vfs.delete_vfolder(vfid)
