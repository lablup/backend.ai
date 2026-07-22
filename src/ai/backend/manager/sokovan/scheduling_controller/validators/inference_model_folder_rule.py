"""INFERENCE-session model-folder presence validator."""

from __future__ import annotations

from typing import override

from ai.backend.common.types import SessionTypes, VFolderUsageMode
from ai.backend.manager.data.session.spec import SessionSpec
from ai.backend.manager.errors.api import InvalidAPIParameters
from ai.backend.manager.sokovan.scheduling_controller.validators.session_spec_base import (
    SessionSpecValidatorRule,
)
from ai.backend.manager.views.sokovan.session_creation import (
    SessionSpecContext,
)


class InferenceModelFolderRule(SessionSpecValidatorRule):
    """INFERENCE sessions must include at least one MODEL-usage vfolder.

    Scans every kernel's resolved ``vfolder_mounts`` — the check
    succeeds as soon as any kernel carries a MODEL mount. Runs against
    the ``usage_mode`` stamped on each :class:`VFolderMount` by the
    scheduler repository's mount resolver, so no extra context map is
    needed.
    """

    @override
    def name(self) -> str:
        return "inference_model_folder"

    @override
    def validate(
        self,
        spec: SessionSpec,
        _context: SessionSpecContext,
    ) -> None:
        if spec.resource_spec.classification.session_type != SessionTypes.INFERENCE:
            return
        for kernel in spec.resource_spec.kernel_specs:
            for mount in kernel.vfolder_mounts:
                if mount.usage_mode == VFolderUsageMode.MODEL:
                    return
        raise InvalidAPIParameters(
            extra_msg=("Inference session requires at least one vfolder with usage_mode=MODEL."),
        )
