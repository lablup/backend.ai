"""VFolder adapter bridging DTOs and Processors."""

from __future__ import annotations

import secrets
from uuid import UUID

from ai.backend.common.contexts.user import current_user
from ai.backend.common.data.model_deployment.types import DeploymentStrategy
from ai.backend.common.dto.manager.v2.common import BinarySizeInfo
from ai.backend.common.dto.manager.v2.deployment.request import DeploymentStrategyInput
from ai.backend.common.dto.manager.v2.vfolder.request import (
    BulkDeleteVFoldersInput,
    BulkPurgeVFoldersInput,
    CloneVFolderInput,
    CreateDownloadSessionInput,
    CreateUploadSessionInput,
    CreateVFolderInput,
    DeleteFilesInput,
    DeployVFolderInput,
    ListFilesInput,
    MkdirInput,
    MoveFileInput,
    SearchVFoldersInput,
    VFolderFilter,
    VFolderOrder,
)
from ai.backend.common.dto.manager.v2.vfolder.response import (
    BulkDeleteVFoldersPayload,
    BulkPurgeVFoldersPayload,
    CloneVFolderPayload,
    CreateDownloadSessionPayload,
    CreateUploadSessionPayload,
    CreateVFolderPayload,
    DeleteFilesPayload,
    DeleteVFolderPayload,
    DeployVFolderPayload,
    FileEntryNode,
    ListFilesPayload,
    MkdirPayload,
    MoveFilePayload,
    PurgeVFolderPayload,
    SearchVFoldersPayload,
    VFolderNode,
)
from ai.backend.common.dto.manager.v2.vfolder.types import (
    FileEntryType,
    VFolderAccessControlInfo,
    VFolderMetadataInfo,
    VFolderOwnershipInfo,
)
from ai.backend.common.dto.manager.v2.vfolder.types import (
    VFolderUsageInfo as VFolderUsageInfoDTO,
)
from ai.backend.common.exception import UnreachableError
from ai.backend.common.types import BinarySize, ClusterMode, RuntimeVariant, VFolderUsageMode
from ai.backend.manager.api.adapters.pagination import PaginationSpec
from ai.backend.manager.data.deployment.creator import (
    DeploymentPolicyConfig,
    ModelRevisionCreator,
    NewDeploymentCreator,
    VFolderMountsCreator,
)
from ai.backend.manager.data.deployment.types import (
    DeploymentMetadata,
    DeploymentNetworkSpec,
    ExecutionSpec,
    ReplicaSpec,
    ResourceSpec,
)
from ai.backend.manager.data.vfolder.types import (
    VFolderData,
    VFolderOperationStatus,
)
from ai.backend.manager.errors.resource import NotAModelVFolder
from ai.backend.manager.errors.storage import VFolderNotFound
from ai.backend.manager.models.deployment_policy import BlueGreenSpec, RollingUpdateSpec
from ai.backend.manager.models.vfolder import VFolderPermission
from ai.backend.manager.models.vfolder.conditions import VFolderConditions
from ai.backend.manager.models.vfolder.orders import (
    DEFAULT_BACKWARD_ORDER as VFOLDER_DEFAULT_BACKWARD_ORDER,
)
from ai.backend.manager.models.vfolder.orders import (
    DEFAULT_FORWARD_ORDER as VFOLDER_DEFAULT_FORWARD_ORDER,
)
from ai.backend.manager.models.vfolder.orders import (
    TIEBREAKER_ORDER as VFOLDER_TIEBREAKER_ORDER,
)
from ai.backend.manager.models.vfolder.orders import (
    resolve_order as resolve_vfolder_order,
)
from ai.backend.manager.repositories.base import (
    QueryCondition,
    QueryOrder,
    combine_conditions_or,
    negate_conditions,
)
from ai.backend.manager.repositories.vfolder.types import (
    ProjectVFolderSearchScope,
    UserVFolderSearchScope,
)
from ai.backend.manager.services.deployment.actions.create_deployment import CreateDeploymentAction
from ai.backend.manager.services.vfolder.actions.admin_search_vfolders import (
    AdminSearchVFoldersAction,
)
from ai.backend.manager.services.vfolder.actions.batch_load_by_ids import (
    BatchLoadVFoldersByIdsAction,
)
from ai.backend.manager.services.vfolder.actions.create_v2 import CreateVFolderV2Action
from ai.backend.manager.services.vfolder.actions.file_v2 import (
    CloneVFolderV2Action,
    CreateDownloadSessionV2Action,
    DeleteFilesV2Action,
    ListFilesV2Action,
    MkdirV2Action,
    MoveFileV2Action,
)
from ai.backend.manager.services.vfolder.actions.search_in_project import (
    SearchVFoldersInProjectAction,
)
from ai.backend.manager.services.vfolder.actions.search_user_vfolders import (
    SearchUserVFoldersAction,
)
from ai.backend.manager.services.vfolder.actions.upload_session_v2 import (
    CreateUploadSessionV2Action,
)
from ai.backend.manager.services.vfolder.actions.vfolder_v2 import (
    DeleteVFolderV2Action,
    PurgeVFolderV2Action,
)

from .base import BaseAdapter

_VFOLDER_PAGINATION_SPEC = PaginationSpec(
    forward_order=VFOLDER_DEFAULT_FORWARD_ORDER,
    backward_order=VFOLDER_DEFAULT_BACKWARD_ORDER,
    forward_condition_factory=VFolderConditions.by_cursor_forward,
    backward_condition_factory=VFolderConditions.by_cursor_backward,
    tiebreaker_order=VFOLDER_TIEBREAKER_ORDER,
)


def _to_binary_size_info(value: int) -> BinarySizeInfo:
    """Convert bytes integer to BinarySizeInfo DTO."""
    return BinarySizeInfo(value=value, display=f"{BinarySize(value):s}")


def _build_policy_from_strategy_input(
    strategy_input: DeploymentStrategyInput | None,
) -> DeploymentPolicyConfig | None:
    """Convert a DeploymentStrategyInput DTO to DeploymentPolicyConfig.

    Returns ``None`` when the caller did not provide a strategy. The deployment
    service will then fall back to the preset's strategy default (if any).
    """
    if strategy_input is None:
        return None
    strategy_spec: RollingUpdateSpec | BlueGreenSpec
    match strategy_input.type:
        case DeploymentStrategy.ROLLING:
            rolling = strategy_input.rolling_update
            if rolling is not None:
                strategy_spec = RollingUpdateSpec(
                    max_surge=rolling.max_surge,
                    max_unavailable=rolling.max_unavailable,
                )
            else:
                strategy_spec = RollingUpdateSpec()
        case DeploymentStrategy.BLUE_GREEN:
            bg = strategy_input.blue_green
            if bg is not None:
                strategy_spec = BlueGreenSpec(
                    auto_promote=bg.auto_promote,
                    promote_delay_seconds=bg.promote_delay_seconds,
                )
            else:
                strategy_spec = BlueGreenSpec()
    return DeploymentPolicyConfig(
        strategy=strategy_input.type,
        strategy_spec=strategy_spec,
    )


class VFolderAdapter(BaseAdapter):
    """Adapter for VFolder domain operations."""

    @staticmethod
    def _vfolder_data_to_node(data: VFolderData) -> VFolderNode:
        """Convert VFolderData to VFolderNode DTO."""
        return VFolderNode(
            id=data.id,
            status=data.status.to_field(),
            host=data.host,
            metadata=VFolderMetadataInfo(
                name=data.name,
                usage_mode=data.usage_mode,
                quota_scope_id=str(data.quota_scope_id) if data.quota_scope_id else None,
                created_at=data.created_at,
                last_used=data.last_used,
                cloneable=data.cloneable,
            ),
            access_control=VFolderAccessControlInfo(
                permission=data.permission.to_field() if data.permission else None,
                ownership_type=data.ownership_type.to_field(),
            ),
            ownership=VFolderOwnershipInfo(
                user_id=data.user,
                project_id=data.group,
                creator_id=data.creator_id,
                creator_email=data.creator,
            ),
            usage=VFolderUsageInfoDTO(
                num_files=data.num_files,
                used_bytes=_to_binary_size_info(data.cur_size),
                max_size=_to_binary_size_info(data.max_size) if data.max_size is not None else None,
                max_files=data.max_files,
            ),
            unmanaged_path=data.unmanaged_path,
        )

    # -------------------------------------------------------------------------
    # Batch load (DataLoader)
    # -------------------------------------------------------------------------

    async def batch_load_by_ids(self, ids: list[UUID]) -> list[VFolderNode | None]:
        """Batch fetch vfolders by IDs for GraphQL DataLoader.

        Used by field resolvers (e.g. ``ModelCardGQL.vfolder``) that surface a
        related vfolder for an entity that is already accessible to the caller.
        Returns nodes in the same order as the input IDs; missing entries are
        ``None``.
        """
        if not ids:
            return []
        action_result = await self._processors.vfolder.batch_load_vfolders_by_ids.wait_for_complete(
            BatchLoadVFoldersByIdsAction(ids=list(ids))
        )
        return [
            self._vfolder_data_to_node(item) if item is not None else None
            for item in action_result.data
        ]

    # -------------------------------------------------------------------------
    # Search
    # -------------------------------------------------------------------------

    async def admin_search(
        self,
        input: SearchVFoldersInput,
    ) -> SearchVFoldersPayload:
        """Admin search for VFolders with system scope."""
        conditions = self._convert_vfolder_filter(input.filter) if input.filter else []
        orders = self._convert_vfolder_orders(input.order) if input.order else []
        querier = self._build_querier(
            conditions=conditions,
            orders=orders,
            pagination_spec=_VFOLDER_PAGINATION_SPEC,
            first=input.first,
            after=input.after,
            last=input.last,
            before=input.before,
            limit=input.limit,
            offset=input.offset,
        )
        action_result = (
            await self._processors.vfolder_admin.admin_search_vfolders.wait_for_complete(
                AdminSearchVFoldersAction(querier=querier)
            )
        )
        return SearchVFoldersPayload(
            items=[self._vfolder_data_to_node(item) for item in action_result.data],
            total_count=action_result.total_count,
            has_next_page=action_result.has_next_page,
            has_previous_page=action_result.has_previous_page,
        )

    async def my_search(
        self,
        input: SearchVFoldersInput,
    ) -> SearchVFoldersPayload:
        """Search vfolders accessible to the current user.

        Calls current_user() internally -- the caller does not need to pass scope.
        """
        me = current_user()
        if me is None:
            raise UnreachableError("User context is not available")
        scope = UserVFolderSearchScope(user_id=me.user_id)
        conditions = self._convert_vfolder_filter(input.filter) if input.filter else []
        orders = self._convert_vfolder_orders(input.order) if input.order else []
        querier = self._build_querier(
            conditions=conditions,
            orders=orders,
            pagination_spec=_VFOLDER_PAGINATION_SPEC,
            first=input.first,
            after=input.after,
            last=input.last,
            before=input.before,
            limit=input.limit,
            offset=input.offset,
        )
        action_result = await self._processors.vfolder.search_user_vfolders.wait_for_complete(
            SearchUserVFoldersAction(scope=scope, querier=querier)
        )
        return SearchVFoldersPayload(
            items=[self._vfolder_data_to_node(item) for item in action_result.data],
            total_count=action_result.total_count,
            has_next_page=action_result.has_next_page,
            has_previous_page=action_result.has_previous_page,
        )

    async def project_search(
        self,
        project_id: UUID,
        input: SearchVFoldersInput,
    ) -> SearchVFoldersPayload:
        """Search vfolders within a project scope.

        Used for the project admin page.
        """
        scope = ProjectVFolderSearchScope(project_id=project_id)
        conditions = self._convert_vfolder_filter(input.filter) if input.filter else []
        orders = self._convert_vfolder_orders(input.order) if input.order else []
        querier = self._build_querier(
            conditions=conditions,
            orders=orders,
            pagination_spec=_VFOLDER_PAGINATION_SPEC,
            first=input.first,
            after=input.after,
            last=input.last,
            before=input.before,
            limit=input.limit,
            offset=input.offset,
        )
        action_result = await self._processors.vfolder.search_vfolders_in_project.wait_for_complete(
            SearchVFoldersInProjectAction(scope=scope, querier=querier)
        )
        return SearchVFoldersPayload(
            items=[self._vfolder_data_to_node(item) for item in action_result.data],
            total_count=action_result.total_count,
            has_next_page=action_result.has_next_page,
            has_previous_page=action_result.has_previous_page,
        )

    async def create(self, input: CreateVFolderInput) -> CreateVFolderPayload:
        """Create a new vfolder."""
        me = current_user()
        if me is None:
            raise UnreachableError("User context is not available")
        action = CreateVFolderV2Action(
            name=input.name,
            user_id=me.user_id,
            domain_name=me.domain_name,
            project_id=input.project_id,
            host=input.host,
            usage_mode=VFolderUsageMode(input.usage_mode.value),
            permission=VFolderPermission(input.permission.value),
            cloneable=input.cloneable,
        )
        result = await self._processors.vfolder.create_vfolder_v2.wait_for_complete(action)
        return CreateVFolderPayload(vfolder=self._vfolder_data_to_node(result.vfolder))

    async def create_upload_session(
        self, vfolder_id: UUID, input: CreateUploadSessionInput
    ) -> CreateUploadSessionPayload:
        """Create an upload session for a vfolder."""
        me = current_user()
        if me is None:
            raise UnreachableError("User context is not available")
        action = CreateUploadSessionV2Action(
            user_id=me.user_id,
            vfolder_id=vfolder_id,
            path=input.path,
            size=input.size,
        )
        result = await self._processors.vfolder.create_upload_session_v2.wait_for_complete(action)
        return CreateUploadSessionPayload(token=result.token, url=result.url)

    async def get(self, vfolder_id: UUID) -> VFolderNode:
        """Get a single vfolder by ID."""
        conditions: list[QueryCondition] = [VFolderConditions.by_id(vfolder_id)]
        querier = self._build_querier(
            conditions=conditions,
            orders=[],
            pagination_spec=_VFOLDER_PAGINATION_SPEC,
            limit=1,
        )
        result = await self._processors.vfolder_admin.admin_search_vfolders.wait_for_complete(
            AdminSearchVFoldersAction(querier=querier)
        )
        if not result.data:
            raise VFolderNotFound()
        return self._vfolder_data_to_node(result.data[0])

    async def delete(self, vfolder_id: UUID) -> DeleteVFolderPayload:
        """Soft-delete a vfolder (move to trash)."""
        me = current_user()
        if me is None:
            raise UnreachableError("User context is not available")
        action = DeleteVFolderV2Action(user_id=me.user_id, vfolder_id=vfolder_id)
        await self._processors.vfolder.delete_v2.wait_for_complete(action)
        return DeleteVFolderPayload(id=vfolder_id)

    async def purge(self, vfolder_id: UUID) -> PurgeVFolderPayload:
        """Permanently delete a vfolder."""
        me = current_user()
        if me is None:
            raise UnreachableError("User context is not available")
        action = PurgeVFolderV2Action(user_id=me.user_id, vfolder_id=vfolder_id)
        await self._processors.vfolder.purge_v2.wait_for_complete(action)
        return PurgeVFolderPayload(id=vfolder_id)

    async def deploy(
        self,
        vfolder_id: UUID,
        input: DeployVFolderInput,
    ) -> DeployVFolderPayload:
        """Create a deployment directly from a model VFolder.

        The VFolder must have ``usage_mode == VFolderUsageMode.MODEL``;
        non-model vfolders are rejected with :class:`NotAModelVFolder`.
        The revision preset supplies image, runtime variant, resource
        slots, environ, startup command, and (optionally) deployment-
        level defaults. Explicit overrides on ``DeployVFolderInput``
        take precedence over the preset default.
        """
        me = current_user()
        if me is None:
            raise UnreachableError("User context is not available")

        batch_result = await self._processors.vfolder.batch_load_vfolders_by_ids.wait_for_complete(
            BatchLoadVFoldersByIdsAction(ids=[vfolder_id])
        )
        if not batch_result.data or batch_result.data[0] is None:
            raise VFolderNotFound()
        vfolder = batch_result.data[0]
        if vfolder.usage_mode != VFolderUsageMode.MODEL:
            raise NotAModelVFolder()

        # Build optional override values; leaving them ``None`` lets the
        # deployment service fall back to the preset default.
        replica_spec: ReplicaSpec | None = None
        if input.replica_count is not None:
            replica_spec = ReplicaSpec(replica_count=input.replica_count)
        elif input.desired_replica_count != 1:
            replica_spec = ReplicaSpec(replica_count=input.desired_replica_count)

        network_spec: DeploymentNetworkSpec | None = None
        if input.open_to_public is not None:
            network_spec = DeploymentNetworkSpec(open_to_public=input.open_to_public)

        policy = _build_policy_from_strategy_input(input.deployment_strategy)

        creator = NewDeploymentCreator(
            metadata=DeploymentMetadata(
                name=f"{vfolder.name}-{secrets.token_hex(4)}",
                domain=vfolder.domain_name,
                project=input.project_id,
                resource_group=input.resource_group,
                created_user=me.user_id,
                session_owner=me.user_id,
                created_at=None,
                revision_history_limit=input.revision_history_limit,
            ),
            replica_spec=replica_spec,
            network=network_spec,
            model_revision=ModelRevisionCreator(
                image_id=None,
                resource_spec=ResourceSpec(
                    cluster_mode=ClusterMode.SINGLE_NODE,
                    cluster_size=1,
                    resource_slots={},
                ),
                mounts=VFolderMountsCreator(
                    model_vfolder_id=vfolder.id,
                ),
                execution=ExecutionSpec(runtime_variant=RuntimeVariant("custom")),
                model_definition=None,
                revision_preset_id=input.revision_preset_id,
            ),
            policy=policy,
        )

        result = await self._processors.deployment.create_deployment.wait_for_complete(
            CreateDeploymentAction(creator=creator)
        )
        return DeployVFolderPayload(
            deployment_id=result.data.id,
            deployment_name=result.data.metadata.name,
        )

    async def bulk_delete(self, input: BulkDeleteVFoldersInput) -> BulkDeleteVFoldersPayload:
        """Soft-delete multiple vfolders."""
        me = current_user()
        if me is None:
            raise UnreachableError("User context is not available")
        for vfolder_id in input.ids:
            action = DeleteVFolderV2Action(user_id=me.user_id, vfolder_id=vfolder_id)
            await self._processors.vfolder.delete_v2.wait_for_complete(action)
        return BulkDeleteVFoldersPayload(deleted_count=len(input.ids))

    async def bulk_purge(self, input: BulkPurgeVFoldersInput) -> BulkPurgeVFoldersPayload:
        """Permanently purge multiple vfolders."""
        me = current_user()
        if me is None:
            raise UnreachableError("User context is not available")
        for vfolder_id in input.ids:
            action = PurgeVFolderV2Action(user_id=me.user_id, vfolder_id=vfolder_id)
            await self._processors.vfolder.purge_v2.wait_for_complete(action)
        return BulkPurgeVFoldersPayload(purged_count=len(input.ids))

    async def list_files(self, vfolder_id: UUID, input: ListFilesInput) -> ListFilesPayload:
        """List files in a vfolder."""
        me = current_user()
        if me is None:
            raise UnreachableError("User context is not available")
        action = ListFilesV2Action(user_id=me.user_id, vfolder_id=vfolder_id, path=input.path)
        result = await self._processors.vfolder_file.list_files_v2.wait_for_complete(action)
        return ListFilesPayload(
            items=[
                FileEntryNode(
                    name=f.name,
                    type=FileEntryType(f.type),
                    size=f.size,
                    mode=int(f.mode),
                    created_at=str(f.created),
                    updated_at=str(f.modified),
                )
                for f in result.files
            ]
        )

    async def mkdir(self, vfolder_id: UUID, input: MkdirInput) -> MkdirPayload:
        """Create directories in a vfolder."""
        me = current_user()
        if me is None:
            raise UnreachableError("User context is not available")
        action = MkdirV2Action(
            user_id=me.user_id,
            vfolder_id=vfolder_id,
            path=input.path,
            parents=input.parents,
            exist_ok=input.exist_ok,
        )
        await self._processors.vfolder_file.mkdir_v2.wait_for_complete(action)
        paths = [input.path] if isinstance(input.path, str) else input.path
        return MkdirPayload(results=paths)

    async def move_file(self, vfolder_id: UUID, input: MoveFileInput) -> MoveFilePayload:
        """Move a file within a vfolder."""
        me = current_user()
        if me is None:
            raise UnreachableError("User context is not available")
        action = MoveFileV2Action(
            user_id=me.user_id, vfolder_id=vfolder_id, src=input.src, dst=input.dst
        )
        await self._processors.vfolder_file.move_file_v2.wait_for_complete(action)
        return MoveFilePayload(src=input.src, dst=input.dst)

    async def delete_files(self, vfolder_id: UUID, input: DeleteFilesInput) -> DeleteFilesPayload:
        """Delete files in a vfolder."""
        me = current_user()
        if me is None:
            raise UnreachableError("User context is not available")
        action = DeleteFilesV2Action(
            user_id=me.user_id,
            vfolder_id=vfolder_id,
            files=input.files,
            recursive=input.recursive,
        )
        result = await self._processors.vfolder_file.delete_files_v2.wait_for_complete(action)
        return DeleteFilesPayload(bgtask_id=result.bgtask_id)

    async def create_download_session(
        self, vfolder_id: UUID, input: CreateDownloadSessionInput
    ) -> CreateDownloadSessionPayload:
        """Create a download session."""
        me = current_user()
        if me is None:
            raise UnreachableError("User context is not available")
        action = CreateDownloadSessionV2Action(
            user_id=me.user_id,
            vfolder_id=vfolder_id,
            path=input.path,
            archive=input.archive,
        )
        result = await self._processors.vfolder_file.download_file_v2.wait_for_complete(action)
        return CreateDownloadSessionPayload(token=result.token, url=result.url)

    async def clone(self, vfolder_id: UUID, input: CloneVFolderInput) -> CloneVFolderPayload:
        """Clone a vfolder."""
        me = current_user()
        if me is None:
            raise UnreachableError("User context is not available")
        action = CloneVFolderV2Action(
            user_id=me.user_id,
            vfolder_id=vfolder_id,
            target_name=input.name,
            target_host=input.host,
        )
        result = await self._processors.vfolder.clone_v2.wait_for_complete(action)
        # Fetch the newly created vfolder for the response
        cloned_vfolder = await self.get(result.new_vfolder_id)
        return CloneVFolderPayload(
            vfolder=cloned_vfolder,
            bgtask_id=result.bgtask_id or "",
        )

    # -------------------------------------------------------------------------
    # Filter / Order conversion
    # -------------------------------------------------------------------------

    def _convert_vfolder_filter(self, f: VFolderFilter) -> list[QueryCondition]:
        conditions: list[QueryCondition] = []
        if f.name is not None:
            c = self.convert_string_filter(
                f.name,
                contains_factory=VFolderConditions.by_name_contains,
                equals_factory=VFolderConditions.by_name_equals,
                starts_with_factory=VFolderConditions.by_name_starts_with,
                ends_with_factory=VFolderConditions.by_name_ends_with,
                in_factory=VFolderConditions.by_name_in,
            )
            if c is not None:
                conditions.append(c)
        if f.host is not None:
            c = self.convert_string_filter(
                f.host,
                contains_factory=VFolderConditions.by_host_contains,
                equals_factory=VFolderConditions.by_host_equals,
                starts_with_factory=VFolderConditions.by_host_starts_with,
                ends_with_factory=VFolderConditions.by_host_ends_with,
                in_factory=VFolderConditions.by_host_in,
            )
            if c is not None:
                conditions.append(c)
        if f.status is not None:
            if f.status.in_ is not None:
                status_values = [VFolderOperationStatus(s) for s in f.status.in_]
                conditions.append(VFolderConditions.by_status_in(status_values))
            if f.status.not_in is not None:
                status_values = [VFolderOperationStatus(s) for s in f.status.not_in]
                conditions.append(VFolderConditions.by_status_not_in(status_values))
        if f.usage_mode is not None:
            if f.usage_mode.in_ is not None:
                mode_values = [VFolderUsageMode(m) for m in f.usage_mode.in_]
                conditions.append(VFolderConditions.by_usage_mode_in(mode_values))
            if f.usage_mode.not_in is not None:
                mode_values = [VFolderUsageMode(m) for m in f.usage_mode.not_in]
                conditions.append(VFolderConditions.by_usage_mode_not_in(mode_values))
        if f.created_at is not None:
            c = f.created_at.build_query_condition(
                before_factory=VFolderConditions.by_created_at_before,
                after_factory=VFolderConditions.by_created_at_after,
                equals_factory=VFolderConditions.by_created_at_equals,
            )
            if c is not None:
                conditions.append(c)
        if f.cloneable is not None:
            conditions.append(VFolderConditions.by_cloneable(f.cloneable))
        if f.AND:
            for sub in f.AND:
                conditions.extend(self._convert_vfolder_filter(sub))
        if f.OR:
            or_conditions: list[QueryCondition] = []
            for sub in f.OR:
                or_conditions.extend(self._convert_vfolder_filter(sub))
            if or_conditions:
                conditions.append(combine_conditions_or(or_conditions))
        if f.NOT:
            not_conditions: list[QueryCondition] = []
            for sub in f.NOT:
                not_conditions.extend(self._convert_vfolder_filter(sub))
            if not_conditions:
                conditions.append(negate_conditions(not_conditions))
        return conditions

    @staticmethod
    def _convert_vfolder_orders(orders: list[VFolderOrder]) -> list[QueryOrder]:
        return [resolve_vfolder_order(o.field, o.direction) for o in orders]
