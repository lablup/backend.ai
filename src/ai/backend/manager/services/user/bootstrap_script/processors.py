from __future__ import annotations

from ai.backend.manager.actions.registry.field import LookupFieldGroup
from ai.backend.manager.actions.v2.field.bulk_processor import PartialBulkFieldActionProcessor
from ai.backend.manager.actions.v2.field.processor import SingleFieldActionProcessor
from ai.backend.manager.actions.v2.ops.result import (
    CreatedFieldOpsResult,
    EntityOpsResult,
    ScopedFieldsOpsResult,
)
from ai.backend.manager.actions.v2.scope.processor import ScopeActionProcessor
from ai.backend.manager.actions.v2.single_entity.processor import SingleEntityActionProcessor
from ai.backend.manager.data.bootstrap_script.types import BootstrapScriptData
from ai.backend.manager.services.user.bootstrap_script.actions.bulk_get import (
    BulkGetBootstrapScriptsAction,
)
from ai.backend.manager.services.user.bootstrap_script.actions.create import (
    CreateBootstrapScriptAction,
)
from ai.backend.manager.services.user.bootstrap_script.actions.get import GetBootstrapScriptAction
from ai.backend.manager.services.user.bootstrap_script.actions.purge import (
    PurgeBootstrapScriptAction,
)
from ai.backend.manager.services.user.bootstrap_script.actions.search import (
    SearchBootstrapScriptsAction,
)
from ai.backend.manager.services.user.bootstrap_script.actions.switch_default import (
    SwitchDefaultBootstrapScriptAction,
    SwitchDefaultBootstrapScriptActionResult,
)
from ai.backend.manager.services.user.bootstrap_script.actions.update import (
    UpdateBootstrapScriptAction,
)
from ai.backend.manager.services.user.service import UserService


class BootstrapScriptProcessors:
    """A bootstrap script is a field row of the user it is set on, and that user answers
    for every operation. Only switching the default runs a service: it writes two rows."""

    create: SingleEntityActionProcessor[
        CreateBootstrapScriptAction, CreatedFieldOpsResult[BootstrapScriptData]
    ]
    get: SingleFieldActionProcessor[GetBootstrapScriptAction, EntityOpsResult[BootstrapScriptData]]
    bulk_get: PartialBulkFieldActionProcessor[BulkGetBootstrapScriptsAction, BootstrapScriptData]
    search: ScopeActionProcessor[
        SearchBootstrapScriptsAction, ScopedFieldsOpsResult[BootstrapScriptData]
    ]
    update: SingleFieldActionProcessor[
        UpdateBootstrapScriptAction, EntityOpsResult[BootstrapScriptData]
    ]
    switch_default: SingleFieldActionProcessor[
        SwitchDefaultBootstrapScriptAction, SwitchDefaultBootstrapScriptActionResult
    ]
    purge: SingleFieldActionProcessor[
        PurgeBootstrapScriptAction, EntityOpsResult[BootstrapScriptData]
    ]

    def __init__(
        self,
        scripts: LookupFieldGroup[BootstrapScriptData],
        user_service: UserService,
    ) -> None:
        self.create = scripts.create_ops(CreateBootstrapScriptAction)
        self.get = scripts.get_ops(GetBootstrapScriptAction)
        self.bulk_get = scripts.partial_bulk_get_ops(BulkGetBootstrapScriptsAction)
        self.search = scripts.search_ops(SearchBootstrapScriptsAction)
        self.update = scripts.update_ops(UpdateBootstrapScriptAction)
        self.switch_default = scripts.single_field(
            SwitchDefaultBootstrapScriptAction, user_service.switch_default_bootstrap_script
        )
        self.purge = scripts.purge_ops(PurgeBootstrapScriptAction)
