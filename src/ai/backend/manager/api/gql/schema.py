import strawberry
from strawberry.federation import Schema
from strawberry.schema.config import StrawberryConfig

from .artifact import (
    approve_artifact_revision,
    artifact,
    artifact_import_progress_updated,
    artifact_revision,
    artifact_revisions,
    artifact_status_changed,
    artifacts,
    cancel_import_artifact,
    cleanup_artifact_revisions,
    import_artifacts,
    reject_artifact_revision,
    scan_artifact_models,
    scan_artifacts,
    update_artifact,
)
from .artifact_registry import default_artifact_registry
from .huggingface_registry import (
    create_huggingface_registry,
    delete_huggingface_registry,
    huggingface_registries,
    huggingface_registry,
    update_huggingface_registry,
)
from .model_deployment.model_deployment import (
    create_model_deployment,
    delete_model_deployment,
    deployment,
    deployment_status_changed,
    deployments,
    replica,
    replica_status_changed,
    update_model_deployment,
)
from .model_deployment.model_revision import (
    create_model_revision,
    revision,
    revisions,
)
from .object_storage import (
    create_object_storage,
    delete_object_storage,
    get_presigned_download_url,
    get_presigned_upload_url,
    object_storage,
    object_storages,
    register_object_storage_bucket,
    unregister_object_storage_bucket,
    update_object_storage,
)
from .reservoir_registry import (
    create_reservoir_registry,
    delete_reservoir_registry,
    reservoir_registries,
    reservoir_registry,
    update_reservoir_registry,
)


@strawberry.type
class Query:
    artifact = artifact
    artifacts = artifacts
    artifact_revision = artifact_revision
    artifact_revisions = artifact_revisions
    deployments = deployments
    deployment = deployment
    revisions = revisions
    revision = revision
    replica = replica
    object_storage = object_storage
    object_storages = object_storages
    huggingface_registry = huggingface_registry
    huggingface_registries = huggingface_registries
    reservoir_registry = reservoir_registry
    reservoir_registries = reservoir_registries
    default_artifact_registry = default_artifact_registry


@strawberry.type
class Mutation:
    scan_artifacts = scan_artifacts
    scan_artifact_models = scan_artifact_models
    import_artifacts = import_artifacts
    update_artifact = update_artifact
    cleanup_artifact_revisions = cleanup_artifact_revisions
    cancel_import_artifact = cancel_import_artifact
    create_model_deployment = create_model_deployment
    update_model_deployment = update_model_deployment
    delete_model_deployment = delete_model_deployment
    create_model_revision = create_model_revision
    create_object_storage = create_object_storage
    update_object_storage = update_object_storage
    delete_object_storage = delete_object_storage
    register_object_storage_bucket = register_object_storage_bucket
    unregister_object_storage_bucket = unregister_object_storage_bucket
    create_huggingface_registry = create_huggingface_registry
    update_huggingface_registry = update_huggingface_registry
    delete_huggingface_registry = delete_huggingface_registry
    create_reservoir_registry = create_reservoir_registry
    update_reservoir_registry = update_reservoir_registry
    delete_reservoir_registry = delete_reservoir_registry
    get_presigned_download_url = get_presigned_download_url
    get_presigned_upload_url = get_presigned_upload_url
    approve_artifact_revision = approve_artifact_revision
    reject_artifact_revision = reject_artifact_revision


@strawberry.type
class Subscription:
    artifact_status_changed = artifact_status_changed
    artifact_import_progress_updated = artifact_import_progress_updated
    deployment_status_changed = deployment_status_changed
    replica_status_changed = replica_status_changed


class CustomizedSchema(Schema):
    def as_str(self) -> str:
        sdl = super().as_str()
        sdl = sdl.replace("type PageInfo", "type PageInfo @shareable").replace(
            'import: ["@external", "@key"]', 'import: ["@external", "@key", "@shareable"]'
        )

        return sdl


schema = CustomizedSchema(
    query=Query,
    mutation=Mutation,
    subscription=Subscription,
    config=StrawberryConfig(auto_camel_case=True),
    enable_federation_2=True,
)
