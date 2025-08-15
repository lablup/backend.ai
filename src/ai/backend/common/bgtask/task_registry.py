from collections.abc import Mapping

from .tasks.base import BaseBackgroundTaskFunction, BaseBackgroundTaskFunctionArgs
from .tasks.storage import CloneVFolder, CloneVFolderArgs

TASK_REGISTRY: Mapping[
    str, tuple[type[BaseBackgroundTaskFunctionArgs], type[BaseBackgroundTaskFunction]]
] = {
    CloneVFolder.get_name(): (
        CloneVFolderArgs,
        CloneVFolder,
    ),
}
