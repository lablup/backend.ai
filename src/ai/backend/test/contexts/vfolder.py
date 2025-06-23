from typing import override

from ai.backend.test.contexts.context import BaseTestContext, ContextName
from ai.backend.test.data.vfolder import VFolderMeta
from ai.backend.test.tester.dependency import VFolderDep


class VFolderContext(BaseTestContext[VFolderDep]):
    @override
    @classmethod
    def name(cls) -> ContextName:
        return ContextName.VFOLDER


class CreatedVFolderMetaContext(BaseTestContext[VFolderMeta]):
    @override
    @classmethod
    def name(cls) -> ContextName:
        return ContextName.CREATED_VFOLDER_META
