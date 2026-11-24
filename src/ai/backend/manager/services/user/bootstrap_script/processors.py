from __future__ import annotations

from ai.backend.manager.actions.registry.field import LookupFieldGroup
from ai.backend.manager.actions.registry.group import ProcessorGroup
from ai.backend.manager.actions.v2.field.bulk_processor import PartialBulkFieldActionProcessor
from ai.backend.manager.actions.v2.field.processor import SingleFieldActionProcessor
from ai.backend.manager.actions.v2.ops.result import EntityOpsResult, ScopedFieldsOpsResult
from ai.backend.manager.actions.v2.scope.processor import ScopeActionProcessor
from ai.backend.manager.actions.v2.single_entity.processor import SingleEntityActionProcessor
from ai.backend.manager.data.bootstrap_script.types import (
    BootstrapScriptData,
    BootstrapScriptRevisionData,
)
from ai.backend.manager.data.user.types import UserData
from ai.backend.manager.services.user.bootstrap_script.actions.add_revision import (
    AddBootstrapScriptRevisionAction,
    AddBootstrapScriptRevisionActionResult,
)
from ai.backend.manager.services.user.bootstrap_script.actions.bulk_get import (
    BulkGetBootstrapScriptsAction,
)
from ai.backend.manager.services.user.bootstrap_script.actions.bulk_get_current_revisions import (
    BulkGetCurrentBootstrapScriptRevisionsAction,
)
from ai.backend.manager.services.user.bootstrap_script.actions.create import (
    CreateBootstrapScriptAction,
    CreateBootstrapScriptActionResult,
)
from ai.backend.manager.services.user.bootstrap_script.actions.get import GetBootstrapScriptAction
from ai.backend.manager.services.user.bootstrap_script.actions.purge import (
    PurgeBootstrapScriptAction,
)
from ai.backend.manager.services.user.bootstrap_script.actions.scoped_search import (
    ScopedSearchBootstrapScriptsAction,
)
from ai.backend.manager.services.user.bootstrap_script.actions.switch_default import (
    SwitchDefaultBootstrapScriptAction,
    SwitchDefaultBootstrapScriptActionResult,
)
from ai.backend.manager.services.user.bootstrap_script.actions.unset_default import (
    UnsetDefaultBootstrapScriptAction,
    UnsetDefaultBootstrapScriptActionResult,
)
from ai.backend.manager.services.user.service import UserService


class BootstrapScriptProcessors:
    """The operations naming a script by its id run through ``scripts``, where the entity
    the row is set on answers; ``revisions`` is the same with a revision as the answer.
    The ones naming the user run through ``group``."""

    create: SingleEntityActionProcessor[
        CreateBootstrapScriptAction, CreateBootstrapScriptActionResult
    ]
    add_revision: SingleFieldActionProcessor[
        AddBootstrapScriptRevisionAction, AddBootstrapScriptRevisionActionResult
    ]
    get: SingleFieldActionProcessor[GetBootstrapScriptAction, EntityOpsResult[BootstrapScriptData]]
    bulk_get_ids: PartialBulkFieldActionProcessor[
        BulkGetBootstrapScriptsAction, BootstrapScriptData
    ]
    scoped_search: ScopeActionProcessor[
        ScopedSearchBootstrapScriptsAction, ScopedFieldsOpsResult[BootstrapScriptData]
    ]
    bulk_get_current_revisions: PartialBulkFieldActionProcessor[
        BulkGetCurrentBootstrapScriptRevisionsAction, BootstrapScriptRevisionData
    ]
    switch_default: SingleEntityActionProcessor[
        SwitchDefaultBootstrapScriptAction, SwitchDefaultBootstrapScriptActionResult
    ]
    unset_default: SingleEntityActionProcessor[
        UnsetDefaultBootstrapScriptAction, UnsetDefaultBootstrapScriptActionResult
    ]
    purge: SingleFieldActionProcessor[
        PurgeBootstrapScriptAction, EntityOpsResult[BootstrapScriptData]
    ]

    def __init__(
        self,
        group: ProcessorGroup[UserData],
        scripts: LookupFieldGroup[BootstrapScriptData],
        revisions: LookupFieldGroup[BootstrapScriptRevisionData],
        user_service: UserService,
    ) -> None:
        self.create = group.single_entity(
            CreateBootstrapScriptAction, user_service.create_bootstrap_script
        )
        self.add_revision = scripts.runtime_single_field(
            AddBootstrapScriptRevisionAction, user_service.add_bootstrap_script_revision
        )
        self.get = scripts.runtime_get_ops(GetBootstrapScriptAction)
        self.bulk_get_ids = scripts.partial_bulk_get_ops(BulkGetBootstrapScriptsAction)
        self.scoped_search = scripts.search_ops(ScopedSearchBootstrapScriptsAction)
        self.bulk_get_current_revisions = revisions.partial_bulk_field(
            BulkGetCurrentBootstrapScriptRevisionsAction,
            user_service.bulk_get_current_bootstrap_script_revisions,
        )
        self.switch_default = group.single_entity(
            SwitchDefaultBootstrapScriptAction, user_service.switch_default_bootstrap_script
        )
        self.unset_default = group.single_entity(
            UnsetDefaultBootstrapScriptAction, user_service.unset_default_bootstrap_script
        )
        self.purge = scripts.runtime_purge_ops(PurgeBootstrapScriptAction)
